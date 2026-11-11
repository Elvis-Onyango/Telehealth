from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin_auth.forms import (
    NotificationBroadcastForm,
    SuperadminUserCreationForm,
    SuperadminUserManagementForm,
)
from apps.admin_auth.models import AuditEvent
from apps.messaging.models import Message
from apps.pharmacy.models import Order, OrderItem, Payment, PharmacyItem
from apps.prescriptions.models import MedicalHistory, MedicalReport, Prescription
from apps.users.models import (
    DoctorAvailability,
    DoctorProfile,
    PatientProfile,
    User,
    Weekday,
)
from apps.notifications.models import Notification
from apps.users.permissions import IsPatient
from apps.videoconferencing.models import VideoCall

from .forms import (
    BillingManagementForm,
    DoctorAssignmentForm,
    DoctorProfileManagementForm,
    HospitalAdministratorCreationForm,
    HospitalAdministratorUpdateForm,
    HospitalAppointmentForm,
    HospitalForm,
    PharmacyItemManagementForm,
    PharmacyOrderManagementForm,
)
from .models import Appointment, Billing, Hospital, HospitalAdministrator
from .serializers import AppointmentCreateSerializer, HospitalSerializer


def _hospital_admin_for(user, hospital):
    if user.is_superuser:
        return True
    if user.role != "admin":
        return False
    return HospitalAdministrator.objects.filter(user=user, hospital=hospital).exists()


def _hospital_has_linked_records(hospital):
    return (
        hospital.doctorprofile_set.exists()
        or hospital.appointments.exists()
        or hospital.administrators.exists()
    )


@transaction.atomic
def _delete_empty_hospital(hospital_id):
    hospital = Hospital.objects.select_for_update().get(pk=hospital_id)
    if _hospital_has_linked_records(hospital):
        return False
    hospital.delete()
    return True


def _managed_hospital(user, requested_id=None):
    if user.is_superuser:
        if requested_id:
            return get_object_or_404(Hospital, pk=requested_id)
        return None

    if user.role != "admin":
        raise PermissionDenied
    try:
        assignment = user.hospital_administration
    except HospitalAdministrator.DoesNotExist as error:
        raise PermissionDenied from error
    if requested_id and str(assignment.hospital_id) != str(requested_id):
        raise PermissionDenied
    return assignment.hospital


class HospitalListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        hospitals = Hospital.objects.all()
        if request.user.role == "admin" and not request.user.is_superuser:
            hospital_id = HospitalAdministrator.objects.filter(
                user=request.user
            ).values_list("hospital_id", flat=True).first()
            hospitals = hospitals.filter(pk=hospital_id) if hospital_id else hospitals.none()
        serializer = HospitalSerializer(hospitals, many=True)
        return Response(serializer.data)

class HospitalDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        hospital = get_object_or_404(Hospital, pk=pk)
        if request.user.role == "admin" and not _hospital_admin_for(request.user, hospital):
            raise PermissionDenied
        serializer = HospitalSerializer(hospital)
        return Response(serializer.data)

    def put(self, request, pk):
        hospital = get_object_or_404(Hospital, pk=pk)
        if not _hospital_admin_for(request.user, hospital):
            raise PermissionDenied
        serializer = HospitalSerializer(hospital, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        hospital = get_object_or_404(Hospital, pk=pk)
        if not request.user.is_superuser:
            raise PermissionDenied
        if not _delete_empty_hospital(hospital.pk):
            return Response(
                {"detail": "Hospitals with linked records cannot be deleted."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AppointmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AppointmentCreateSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsPatient()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        appointments = Appointment.objects.filter(is_active=True).select_related(
            "patient__user",
            "doctor__user",
            "doctor__hospital",
        )

        if self.request.user.role == "patient":
            return appointments.filter(patient__user=self.request.user)
        if self.request.user.role == "doctor":
            return appointments.filter(doctor__user=self.request.user)
        return appointments.none()


def _dashboard_context(user, hospital):
    hospitals = Hospital.objects.order_by("name")
    if not user.is_superuser:
        hospitals = hospitals.filter(pk=hospital.pk)

    appointments = Appointment.objects.none()
    doctors = DoctorProfile.objects.none()
    billing_records = Billing.objects.none()
    if hospital:
        appointments = (
            Appointment.objects.filter(is_active=True, hospital=hospital)
            .select_related("patient__user", "doctor__user", "billing")
            .order_by("-date", "-time")
        )
        doctors = DoctorProfile.objects.filter(hospital=hospital).select_related(
            "user"
        ).order_by("user__last_name", "user__first_name")
        billing_records = Billing.objects.filter(appointment__hospital=hospital)
    billing_records = billing_records.select_related(
        "appointment__patient__user",
        "appointment__doctor__user",
    ).order_by("-appointment__date", "-appointment__time")
    hospital_admins = HospitalAdministrator.objects.select_related(
        "user", "hospital"
    ).order_by("hospital__name", "user__last_name")
    if hospital:
        hospital_admins = hospital_admins.filter(hospital=hospital)
    elif not user.is_superuser:
        hospital_admins = hospital_admins.none()

    doctor_rows = [
        {"doctor": doctor, "form": DoctorProfileManagementForm(instance=doctor)}
        for doctor in doctors
    ]
    appointment_rows = [
        {
            "appointment": appointment,
            "form": HospitalAppointmentForm(instance=appointment, hospital=hospital),
        }
        for appointment in appointments
    ]
    billing_rows = [
        {"billing": billing, "form": BillingManagementForm(instance=billing)}
        for billing in billing_records
    ]
    hospital_admin_rows = [
        {
            "assignment": assignment,
            "form": HospitalAdministratorUpdateForm(instance=assignment),
        }
        for assignment in hospital_admins
    ]
    patients = PatientProfile.objects.none()
    hospital_reports = MedicalReport.objects.none()
    hospital_staff = []
    if hospital:
        patients = PatientProfile.objects.filter(
            Q(appointments__hospital=hospital)
            | Q(assigned_doctors__hospital=hospital)
            | Q(primary_doctor__hospital=hospital)
        ).distinct().select_related("user").order_by(
            "user__last_name",
            "user__first_name",
        )
        hospital_reports = MedicalReport.objects.filter(
            patient__in=patients
        ).select_related(
            "patient__user",
            "doctor__user",
        ).order_by("-date_issued")[:50]
        hospital_staff = [
            {"user": doctor.user, "title": doctor.specialization, "kind": "Doctor"}
            for doctor in doctors
        ] + [
            {
                "user": assignment.user,
                "title": assignment.hospital.name,
                "kind": "Hospital administrator",
            }
            for assignment in hospital_admins
        ]

    pharmacy_items = PharmacyItem.objects.order_by("name")
    pharmacy_orders = (
        Order.objects.select_related("user", "payment")
        .prefetch_related("orderitem_set__pharmacy_item")
        .order_by("-ordered_at")
    )

    context = {
        "notifications": Notification.objects.filter(user=user).order_by(
            "-created_at",
            "-pk",
        )[:6],
        "unread_notifications_count": Notification.objects.filter(
            user=user,
            is_read=False,
        ).count(),
        "hospitals": hospitals,
        "hospital_count": hospitals.count(),
        "hospital_admin_count": hospital_admins.count(),
        "selected_hospital": hospital,
        "hospital_admin_rows": hospital_admin_rows,
        "patients": patients[:100],
        "patients_count_total": patients.count(),
        "hospital_staff": hospital_staff,
        "hospital_reports": hospital_reports,
        "pharmacy_items": pharmacy_items[:100],
        "pharmacy_items_count": pharmacy_items.count(),
        "pharmacy_item_form": PharmacyItemManagementForm(),
        "pharmacy_item_rows": [
            {
                "item": item,
                "form": PharmacyItemManagementForm(instance=item),
            }
            for item in pharmacy_items[:100]
        ],
        "pharmacy_orders": pharmacy_orders[:50],
        "pharmacy_order_rows": [
            {"order": order, "form": PharmacyOrderManagementForm(instance=order)}
            for order in pharmacy_orders[:50]
        ],
        "pharmacy_order_count": pharmacy_orders.count(),
        "pharmacy_sales_total": Payment.objects.filter(
            is_successful=True
        ).aggregate(total=Sum("amount"))["total"] or 0,
        "doctors": doctors,
        "doctor_rows": doctor_rows,
        "unassigned_doctors": DoctorProfile.objects.filter(
            hospital__isnull=True
        ).select_related("user").order_by("user__last_name", "user__first_name"),
        "appointments": appointments,
        "appointment_rows": appointment_rows,
        "billing_rows": billing_rows,
        "patients_count": appointments.values("patient_id").distinct().count(),
        "appointments_count": appointments.count(),
        "doctors_count": doctors.count(),
        "paid_total": billing_records.filter(payment_status="paid").aggregate(
            total=Sum("total_fee")
        )["total"] or 0,
        "pending_payments_count": billing_records.filter(
            payment_status="pending"
        ).count(),
        "hospital_form": HospitalForm(),
        "hospital_update_form": HospitalForm(instance=hospital) if hospital else None,
        "hospital_admin_form": HospitalAdministratorCreationForm(),
        "doctor_assignment_form": DoctorAssignmentForm(hospital=hospital)
        if hospital
        else None,
        "appointment_form": HospitalAppointmentForm(hospital=hospital)
        if hospital
        else None,
        "is_superadmin": user.is_superuser,
    }
    if user.is_superuser:
        today = timezone.localdate()
        current_month = today.replace(day=1)
        first_month_index = current_month.year * 12 + current_month.month - 6
        first_month_year, first_month_number = divmod(first_month_index, 12)
        first_month_number += 1
        first_month = today.replace(
            year=first_month_year,
            month=first_month_number,
            day=1,
        )
        next_month_index = current_month.year * 12 + current_month.month
        next_month_year, next_month_number = divmod(next_month_index, 12)
        next_month_number += 1
        next_month = today.replace(
            year=next_month_year,
            month=next_month_number,
            day=1,
        )
        monthly_appointment_counts = {
            row["month"]: row["count"]
            for row in Appointment.objects.filter(
                date__gte=first_month,
                date__lt=next_month,
            )
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(count=Count("pk"))
        }
        appointment_months = []
        for offset in range(6):
            month_index = first_month_year * 12 + first_month_number - 1 + offset
            year, month_number = divmod(month_index, 12)
            month_number += 1
            month_start = today.replace(year=year, month=month_number, day=1)
            appointment_months.append(
                {
                    "label": month_start.strftime("%b"),
                    "count": monthly_appointment_counts.get(month_start, 0),
                }
            )
        max_monthly_appointments = max(
            (month["count"] for month in appointment_months),
            default=0,
        )
        for month in appointment_months:
            month["bar_height"] = (
                max(6, round(month["count"] / max_monthly_appointments * 100))
                if max_monthly_appointments and month["count"]
                else 0
            )

        appointment_status_counts = dict(
            Appointment.objects.values("status")
            .annotate(count=Count("pk"))
            .values_list("status", "count")
        )
        total_appointments = sum(appointment_status_counts.values())
        appointment_status_rows = [
            {
                "label": label,
                "count": appointment_status_counts.get(value, 0),
                "percentage": round(
                    appointment_status_counts.get(value, 0) / total_appointments * 100
                )
                if total_appointments
                else 0,
            }
            for value, label in Appointment.STATUS_CHOICES
        ]
        model_anchors = (
            ("Users", User, "user-directory"),
            ("Patients", PatientProfile, "global-patient-directory"),
            ("Doctors", DoctorProfile, "global-staff-directory"),
            ("Doctor availability", DoctorAvailability, "global-staff-directory"),
            ("Weekdays", Weekday, "global-staff-directory"),
            ("Hospitals", Hospital, "hospital-management"),
            ("Hospital administrators", HospitalAdministrator, "global-staff-directory"),
            ("Appointments", Appointment, "all-appointments"),
            ("Billing", Billing, "global-billing"),
            ("Medical histories", MedicalHistory, "global-clinical-records"),
            ("Prescriptions", Prescription, "global-clinical-records"),
            ("Medical reports", MedicalReport, "global-clinical-records"),
            ("Messages", Message, "global-private-messages"),
            ("Notifications", Notification, "notifications"),
            ("Pharmacy items", PharmacyItem, "pharmacy-management"),
            ("Orders", Order, "pharmacy-management"),
            ("Order items", OrderItem, "pharmacy-management"),
            ("Payments", Payment, "pharmacy-management"),
            ("Video calls", VideoCall, "global-video-calls"),
        )
        context.update(
            {
                "global_model_rows": [
                    {
                        "label": label,
                        "count": model.objects.count(),
                        "anchor": anchor,
                    }
                    for label, model, anchor in model_anchors
                ],
                "global_total_users": User.objects.count(),
                "global_total_appointments": total_appointments,
                "global_active_appointments": Appointment.objects.filter(
                    is_active=True
                ).count(),
                "global_paid_total": Billing.objects.filter(
                    payment_status="paid"
                ).aggregate(total=Sum("total_fee"))["total"] or 0,
                "global_appointment_months": appointment_months,
                "global_appointment_status_rows": appointment_status_rows,
                "global_users": User.objects.order_by("-date_joined")[:10],
                "global_user_rows": [
                    {"user": account, "form": SuperadminUserManagementForm(instance=account)}
                    for account in User.objects.filter(is_superuser=False)
                    .order_by("-date_joined")[:50]
                ],
                "superadmin_user_form": SuperadminUserCreationForm(),
                "global_patients": PatientProfile.objects.select_related(
                    "user"
                ).order_by("-pk")[:20],
                "global_staff": User.objects.filter(
                    Q(doctor_profile__isnull=False)
                    | Q(hospital_administration__isnull=False)
                ).order_by("role", "last_name", "first_name")[:50],
                "global_appointments": Appointment.objects.select_related(
                    "patient__user", "doctor__user", "hospital"
                ).order_by("-created_at")[:10],
                "global_histories": MedicalHistory.objects.select_related(
                    "patient__user"
                ).order_by("-pk")[:10],
                "global_prescriptions": Prescription.objects.select_related(
                    "patient__user", "doctor__user"
                ).order_by("-date_issued")[:10],
                "global_reports": MedicalReport.objects.select_related(
                    "patient__user", "doctor__user"
                ).order_by("-date_issued")[:10],
                "global_messages": Message.objects.select_related(
                    "sender", "recipient"
                ).order_by("-timestamp")[:10],
                "global_orders": Order.objects.select_related(
                    "user"
                ).order_by("-ordered_at")[:10],
                "global_video_calls": VideoCall.objects.select_related(
                    "host", "appointment"
                ).prefetch_related("participants").order_by("-scheduled_time")[:20],
                "global_billing": Billing.objects.select_related(
                    "appointment__patient__user",
                    "appointment__doctor__user",
                    "appointment__hospital",
                ).order_by("-appointment__date", "-appointment__time")[:20],
                "global_audit_events": AuditEvent.objects.select_related(
                    "actor"
                ).all()[:20],
                "notification_broadcast_form": NotificationBroadcastForm(),
            }
        )
    return context


@login_required(login_url="/admin-login/")
def hospital_dashboard(request):
    hospital = _managed_hospital(request.user, request.GET.get("hospital_id"))
    if request.user.is_superuser:
        url = reverse("superadmin-dashboard")
        if hospital:
            return redirect(f"{url}?hospital_id={hospital.pk}")
        return redirect(url)
    AuditEvent.objects.create(
        actor=request.user,
        action="viewed_hospital_dashboard",
        object_type="hospital",
        object_id=str(hospital.pk),
    )
    return render(
        request,
        "appointments/hospital_dashboard.html",
        _dashboard_context(request.user, hospital),
    )


@login_required(login_url="/admin-login/")
def superadmin_dashboard(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    AuditEvent.objects.create(
        actor=request.user,
        action="viewed_dashboard",
        object_type="superadmin_dashboard",
        details={"hospital_id": request.GET.get("hospital_id") or ""},
    )
    hospital = _managed_hospital(request.user, request.GET.get("hospital_id"))
    return render(
        request,
        "appointments/hospital_dashboard.html",
        _dashboard_context(request.user, hospital),
    )


def _dashboard_redirect(request, hospital_id=None):
    if request.user.is_superuser:
        url = reverse("superadmin-dashboard")
        if hospital_id:
            return redirect(f"{url}?hospital_id={hospital_id}")
        return redirect(url)
    return redirect("hospital-dashboard")


@login_required(login_url="/admin-login/")
@require_POST
def dashboard_action(request, action):
    user = request.user
    object_id = request.POST.get("object_id")
    hospital_id = request.POST.get("hospital_id")
    requires_hospital = action not in {
        "create_hospital",
        "create_hospital_admin",
        "update_hospital_admin",
        "delete_hospital",
        "send_notification",
        "create_pharmacy_item",
        "update_pharmacy_item",
        "delete_pharmacy_item",
        "update_pharmacy_order",
        "create_user",
        "update_user",
    }
    hospital = _managed_hospital(user, hospital_id) if requires_hospital else None
    if requires_hospital and hospital is None:
        raise PermissionDenied
    redirect_hospital_id = hospital.pk if hospital else hospital_id

    if action in {"create_user", "update_user"}:
        if not user.is_superuser:
            raise PermissionDenied
        if action == "create_user":
            form = SuperadminUserCreationForm(request.POST)
            if form.is_valid():
                account = form.save()
                AuditEvent.objects.create(
                    actor=user,
                    action="created_user",
                    object_type="user",
                    object_id=str(account.pk),
                    details={"role": account.role},
                )
                messages.success(request, f"{account.get_full_name()} account created.")
            else:
                messages.error(request, form.errors.as_text())
        else:
            account = get_object_or_404(
                User.objects.filter(is_superuser=False),
                pk=object_id,
            )
            if account.pk == user.pk:
                messages.error(request, "You cannot deactivate your own account.")
            else:
                form = SuperadminUserManagementForm(request.POST, instance=account)
                if form.is_valid():
                    account = form.save()
                    AuditEvent.objects.create(
                        actor=user,
                        action="updated_user",
                        object_type="user",
                        object_id=str(account.pk),
                        details={"is_active": account.is_active},
                    )
                    messages.success(request, "User account updated.")
                else:
                    messages.error(request, form.errors.as_text())
    elif action == "send_notification":
        if not user.is_superuser:
            raise PermissionDenied
        form = NotificationBroadcastForm(request.POST)
        if form.is_valid():
            recipients = (
                User.objects.all()
                if form.cleaned_data["broadcast"]
                else User.objects.filter(pk=form.cleaned_data["recipient"].pk)
            )
            notifications = [
                Notification(user=recipient, message=form.cleaned_data["message"])
                for recipient in recipients.iterator()
            ]
            Notification.objects.bulk_create(notifications)
            AuditEvent.objects.create(
                actor=user,
                action="sent_notification",
                object_type="notification",
                details={
                    "recipient_count": len(notifications),
                    "broadcast": form.cleaned_data["broadcast"],
                    "recipient_id": (
                        None
                        if form.cleaned_data["broadcast"]
                        else form.cleaned_data["recipient"].pk
                    ),
                },
            )
            messages.success(
                request,
                f"Notification sent to {len(notifications)} user(s).",
            )
        else:
            messages.error(request, form.errors.as_text())
    elif action in {
        "create_pharmacy_item",
        "update_pharmacy_item",
        "delete_pharmacy_item",
        "update_pharmacy_order",
    }:
        if not user.is_superuser:
            _managed_hospital(user)
        if action == "create_pharmacy_item":
            form = PharmacyItemManagementForm(
                request.POST,
                request.FILES,
            )
            if form.is_valid():
                item = form.save()
                AuditEvent.objects.create(
                    actor=user,
                    action="created_pharmacy_item",
                    object_type="pharmacy_item",
                    object_id=str(item.pk),
                )
                messages.success(request, "Pharmacy item created.")
            else:
                messages.error(request, form.errors.as_text())
        elif action == "update_pharmacy_item":
            item = get_object_or_404(PharmacyItem, pk=object_id)
            form = PharmacyItemManagementForm(
                request.POST,
                request.FILES,
                instance=item,
            )
            if form.is_valid():
                item = form.save()
                AuditEvent.objects.create(
                    actor=user,
                    action="updated_pharmacy_item",
                    object_type="pharmacy_item",
                    object_id=str(item.pk),
                )
                messages.success(request, "Pharmacy item updated.")
            else:
                messages.error(request, form.errors.as_text())
        elif action == "delete_pharmacy_item":
            item = get_object_or_404(PharmacyItem, pk=object_id)
            if OrderItem.objects.filter(pharmacy_item=item).exists():
                messages.error(
                    request,
                    "This item is referenced by an order and cannot be deleted.",
                )
            else:
                item.delete()
                AuditEvent.objects.create(
                    actor=user,
                    action="deleted_pharmacy_item",
                    object_type="pharmacy_item",
                    object_id=str(object_id),
                )
                messages.success(request, "Pharmacy item deleted.")
        else:
            order = get_object_or_404(Order, pk=object_id)
            form = PharmacyOrderManagementForm(request.POST, instance=order)
            if form.is_valid():
                order = form.save()
                AuditEvent.objects.create(
                    actor=user,
                    action="updated_pharmacy_order",
                    object_type="pharmacy_order",
                    object_id=str(order.pk),
                    details={"status": order.status},
                )
                messages.success(request, "Pharmacy order updated.")
            else:
                messages.error(request, form.errors.as_text())
    elif action == "create_hospital":
        if not user.is_superuser:
            raise PermissionDenied
        form = HospitalForm(request.POST)
        if form.is_valid():
            hospital = form.save()
            redirect_hospital_id = hospital.pk
            messages.success(request, "Hospital created.")
        else:
            messages.error(request, form.errors.as_text())
    elif action == "update_hospital":
        hospital = _managed_hospital(user, hospital_id)
        form = HospitalForm(request.POST, instance=hospital)
        if form.is_valid():
            form.save()
            messages.success(request, "Hospital details updated.")
        else:
            messages.error(request, form.errors.as_text())
    elif action == "delete_hospital":
        if not user.is_superuser:
            raise PermissionDenied
        hospital = get_object_or_404(Hospital, pk=hospital_id)
        if not _delete_empty_hospital(hospital.pk):
            messages.error(request, "Unassign linked records before deleting this hospital.")
        else:
            redirect_hospital_id = None
            messages.success(request, "Hospital deleted.")
    elif action == "create_hospital_admin":
        if not user.is_superuser:
            raise PermissionDenied
        form = HospitalAdministratorCreationForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            redirect_hospital_id = assignment.hospital_id
            messages.success(request, "Hospital administrator account created.")
        else:
            messages.error(request, form.errors.as_text())
    elif action == "update_hospital_admin":
        if not user.is_superuser:
            raise PermissionDenied
        assignment = get_object_or_404(
            HospitalAdministrator.objects.select_related("user", "hospital"),
            pk=object_id,
        )
        form = HospitalAdministratorUpdateForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save()
            redirect_hospital_id = assignment.hospital_id
            messages.success(request, "Hospital administrator updated.")
        else:
            redirect_hospital_id = assignment.hospital_id
            messages.error(request, form.errors.as_text())
    elif action == "assign_doctor":
        form = DoctorAssignmentForm(request.POST, hospital=hospital)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor assigned to this hospital.")
        else:
            messages.error(request, form.errors.as_text())
    elif action == "update_doctor":
        doctor = get_object_or_404(DoctorProfile, pk=object_id, hospital=hospital)
        form = DoctorProfileManagementForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor operational details updated.")
        else:
            messages.error(request, form.errors.as_text())
    elif action == "unassign_doctor":
        doctor = get_object_or_404(DoctorProfile, pk=object_id, hospital=hospital)
        doctor.hospital = None
        doctor.save(update_fields=["hospital"])
        messages.success(request, "Doctor unassigned. Historical appointments were retained.")
    elif action == "create_appointment":
        form = HospitalAppointmentForm(request.POST, hospital=hospital)
        if form.is_valid():
            form.save(processed_by=user)
            messages.success(request, "Appointment created.")
        else:
            messages.error(request, form.errors.as_text())
    elif action == "update_appointment":
        appointment = get_object_or_404(
            Appointment,
            pk=object_id,
            hospital=hospital,
            is_active=True,
        )
        form = HospitalAppointmentForm(
            request.POST,
            instance=appointment,
            hospital=hospital,
        )
        if form.is_valid():
            form.save(processed_by=user)
            messages.success(request, "Appointment updated.")
        else:
            messages.error(request, form.errors.as_text())
    elif action == "cancel_appointment":
        appointment = get_object_or_404(
            Appointment,
            pk=object_id,
            hospital=hospital,
            is_active=True,
        )
        appointment.status = "cancelled"
        appointment.is_active = False
        appointment.save(update_fields=["status", "is_active", "updated_at"])
        messages.success(request, "Appointment cancelled; its billing record was retained.")
    elif action == "update_billing":
        billing = get_object_or_404(
            Billing.objects.select_related("appointment"),
            pk=object_id,
            appointment__hospital=hospital,
        )
        form = BillingManagementForm(request.POST, instance=billing)
        if form.is_valid():
            billing = form.save(commit=False)
            billing.processed_by = user
            billing.save()
            messages.success(request, "Billing record updated.")
        else:
            messages.error(request, form.errors.as_text())
    else:
        raise Http404

    return _dashboard_redirect(request, redirect_hospital_id)


class AppointmentBookingForm(View):
    def get(self, request):
        return render(request, "appointments/appointment_booking.html")
