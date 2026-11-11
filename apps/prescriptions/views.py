from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.views import APIView

from apps.admin_auth.models import AuditEvent
from apps.appointments.models import Appointment, HospitalAdministrator
from apps.users.models import DoctorProfile
from apps.users.permissions import IsDoctor, IsPatient

from .forms import MedicalReportCreationForm, SymptomIntakeForm
from .models import MedicalHistory, Prescription, MedicalReport, SymptomIntake, build_visit_summary_pdf
from .serializers import MedicalHistorySerializer, PrescriptionSerializer, MedicalReportSerializer


def _records_for_user(queryset, user):
    if user.is_superuser:
        return queryset
    if user.role == "admin":
        try:
            hospital = user.hospital_administration.hospital
        except HospitalAdministrator.DoesNotExist:
            return queryset.none()
        return queryset.filter(
            Q(patient__appointments__hospital=hospital)
            | Q(patient__assigned_doctors__hospital=hospital)
            | Q(patient__primary_doctor__hospital=hospital)
        ).distinct()
    if hasattr(user, "patient_profile"):
        return queryset.filter(patient__user=user)
    if hasattr(user, "doctor_profile"):
        doctor = user.doctor_profile
        return queryset.filter(
            Q(patient__assigned_doctors=doctor)
            | Q(patient__appointments__doctor=doctor)
        ).distinct()
    return queryset.none()


@login_required(login_url="/api/users/login-page/")
def symptom_intake_page(request, appointment_id):
    if request.user.role != "patient":
        raise DjangoPermissionDenied

    appointment = get_object_or_404(
        Appointment,
        pk=appointment_id,
        patient__user=request.user,
    )

    form = SymptomIntakeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        SymptomIntake.objects.create(
            patient=appointment.patient,
            appointment=appointment,
            primary_symptoms=form.cleaned_data["primary_symptoms"],
            symptom_duration=form.cleaned_data["symptom_duration"],
            severity=form.cleaned_data["severity"],
            associated_factors=form.cleaned_data["associated_factors"],
            notes=form.cleaned_data["notes"],
        )
        messages.success(request, "Your symptom intake has been saved.")
        return redirect("users:patient-dashboard")

    return render(
        request,
        "prescriptions/symptom_intake_form.html",
        {"form": form, "appointment": appointment},
    )


@login_required(login_url="/api/users/login-page/")
def medical_report_create_page(request):
    if request.user.role != "doctor":
        raise DjangoPermissionDenied
    try:
        doctor = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        return redirect("users:doctor-profile-create")

    form = MedicalReportCreationForm(
        request.POST or None,
        request.FILES or None,
        doctor=doctor,
    )
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.doctor = doctor
        report.save()
        AuditEvent.objects.create(
            actor=request.user,
            action="created_medical_report",
            object_type="medical_report",
            object_id=str(report.pk),
            details={"patient_id": report.patient_id},
        )
        messages.success(request, "Lab result or medical report added.")
        return redirect("users:doctor-dashboard")
    return render(request, "prescriptions/medical_report_form.html", {"form": form})


class MedicalHistoryListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsPatient()]
        return super().get_permissions()

    def get_queryset(self):
        return _records_for_user(MedicalHistory.objects.all(), self.request.user)

    def perform_create(self, serializer):
        if not hasattr(self.request.user, "patient_profile"):
            raise PermissionDenied("Only patients can create their medical history.")
        serializer.save(patient=self.request.user.patient_profile)


class MedicalHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _records_for_user(MedicalHistory.objects.all(), self.request.user)

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            return [permissions.IsAuthenticated(), IsPatient()]
        return super().get_permissions()


class PrescriptionListCreateView(generics.ListCreateAPIView):
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Prescription.objects.select_related("patient__user", "doctor__user")
        user = self.request.user
        if self.request.method == "GET" and user.is_superuser:
            return queryset
        if self.request.method == "GET" and hasattr(user, "patient_profile"):
            return queryset.filter(patient__user=user)
        if hasattr(user, "doctor_profile"):
            return queryset.filter(doctor__user=user)
        return queryset.none()

    def get_permissions(self):
        if self.request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            return [permissions.IsAuthenticated(), IsDoctor()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.doctor_profile)


class PrescriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            return [permissions.IsAuthenticated(), IsDoctor()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = Prescription.objects.select_related("patient__user", "doctor__user")
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            return queryset.filter(doctor__user=self.request.user)
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(
            Q(patient__user=self.request.user) | Q(doctor__user=self.request.user)
        )

class MedicalReportListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicalReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _records_for_user(
            MedicalReport.objects.select_related("patient__user", "doctor__user"),
            self.request.user,
        )

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsDoctor()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.doctor_profile)


class MedicalReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicalReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = MedicalReport.objects.select_related("patient__user", "doctor__user")
        if self.request.user.is_superuser and self.request.method == "GET":
            return queryset
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            return queryset.filter(doctor__user=self.request.user)
        return _records_for_user(queryset, self.request.user)

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            return [permissions.IsAuthenticated(), IsDoctor()]
        return super().get_permissions()


class MedicalReportDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        report = get_object_or_404(
            _records_for_user(
                MedicalReport.objects.select_related("patient__user", "doctor__user"),
                request.user,
            ),
            pk=pk,
        )
        if not report.report_file:
            raise NotFound("This medical report has no attached file.")
        if request.user.is_superuser or request.user.role == "admin":
            AuditEvent.objects.create(
                actor=request.user,
                action="downloaded_medical_report",
                object_type="medical_report",
                object_id=str(report.pk),
            )
        return FileResponse(
            report.report_file.open("rb"),
            as_attachment=True,
            filename=Path(report.report_file.name).name,
        )


class VisitSummaryDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, appointment_id):
        appointment = get_object_or_404(
            Appointment,
            pk=appointment_id,
        )

        if request.user.is_superuser or request.user.role == "admin":
            pass
        elif hasattr(request.user, "patient_profile") and appointment.patient.user == request.user:
            pass
        elif hasattr(request.user, "doctor_profile") and appointment.doctor.user == request.user:
            pass
        else:
            raise PermissionDenied("You do not have access to this appointment summary.")

        intake = appointment.symptom_intakes.order_by("-created_at").first()
        report = appointment.medical_reports.order_by("-date_issued").first()
        summary_lines = [
            "Telehealth Visit Summary",
            "=" * 24,
            f"Patient: {appointment.patient.user.get_full_name()}",
            f"Doctor: {appointment.doctor.user.get_full_name()}",
            f"Date: {appointment.date} at {appointment.time}",
            "",
        ]

        if intake:
            summary_lines.extend([
                "Symptoms:",
                f"- {intake.primary_symptoms}",
                f"- Duration: {intake.symptom_duration or 'Not specified'}",
                f"- Severity: {intake.severity.title()}",
                f"- Trigger factors: {intake.associated_factors or 'Not specified'}",
                f"- Notes: {intake.notes or 'No notes provided'}",
                "",
            ])
        else:
            summary_lines.extend(["Symptoms:", "- No intake submitted before this visit.", ""])

        if report:
            summary_lines.extend([
                "Diagnosis:",
                report.get_decrypted_diagnosis() if report.diagnosis else "No diagnosis recorded",
                "",
                "Treatment plan:",
                report.get_decrypted_treatment_plan() if report.treatment_plan else "No treatment plan recorded",
                "",
                "Clinical notes:",
                report.get_decrypted_notes() if report.encrypted_notes else "No clinical notes recorded",
            ])
        else:
            summary_lines.extend(["Diagnosis:", "No clinical report available."])

        pdf_bytes = build_visit_summary_pdf(summary_lines)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="visit-summary-{appointment.pk}.pdf"'
        return response
