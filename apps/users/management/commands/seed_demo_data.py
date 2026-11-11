from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.appointments.models import (
    Appointment,
    Billing,
    Hospital,
    HospitalAdministrator,
)
from apps.users.models import DoctorAvailability, DoctorProfile, PatientProfile, Weekday


HOSPITALS = (
    {
        "key": "central",
        "name": "Central Family Health Centre",
        "address": "Westlands, Nairobi",
        "contact": "+254700000101",
        "email": "central@demo.example.test",
    },
    {
        "key": "lakeside",
        "name": "Lakeside Community Hospital",
        "address": "Milimani, Kisumu",
        "contact": "+254700000102",
        "email": "lakeside@demo.example.test",
    },
    {
        "key": "highlands",
        "name": "Highlands Specialist Clinic",
        "address": "Town Centre, Nakuru",
        "contact": "+254700000103",
        "email": "highlands@demo.example.test",
    },
)

DOCTORS = (
    ("demo_doctor_amina", "Amina", "Njoroge", "Family Medicine", "central", 7, "1800.00", ("monday", "wednesday", "friday")),
    ("demo_doctor_david", "David", "Otieno", "Cardiology", "central", 12, "3500.00", ("tuesday", "thursday")),
    ("demo_doctor_grace", "Grace", "Wanjiku", "Pediatrics", "lakeside", 9, "2200.00", ("monday", "thursday", "saturday")),
    ("demo_doctor_brian", "Brian", "Mwangi", "Dermatology", "lakeside", 5, "2500.00", ("tuesday", "friday")),
    ("demo_doctor_zawadi", "Zawadi", "Kamau", "Internal Medicine", "highlands", 11, "2800.00", ("wednesday", "friday")),
)

PATIENTS = (
    ("demo_patient_joy", "Joy", "Kiptoo", "female"),
    ("demo_patient_peter", "Peter", "Maina", "male"),
    ("demo_patient_nia", "Nia", "Omondi", "female"),
    ("demo_patient_samuel", "Samuel", "Kariuki", "male"),
    ("demo_patient_leah", "Leah", "Achieng", "female"),
    ("demo_patient_musa", "Musa", "Abdi", "male"),
)

ADMINISTRATORS = (
    ("demo_hospital_admin_central", "Faith", "Muthoni", "central"),
    ("demo_hospital_admin_lakeside", "Kevin", "Ochieng", "lakeside"),
    ("demo_hospital_admin_highlands", "Miriam", "Wairimu", "highlands"),
)


class Command(BaseCommand):
    help = "Add fictional, repeatable demo data without changing existing records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            required=True,
            help="Password to set on newly created demo accounts.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]

        User = get_user_model()
        hospitals = {
            entry["key"]: self.get_hospital(entry)
            for entry in HOSPITALS
        }
        weekdays = {
            day: Weekday.objects.get_or_create(day=day)[0]
            for day in (
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            )
        }

        doctors = {}
        for username, first, last, specialty, hospital_key, experience, fee, days in DOCTORS:
            user = self.get_user(
                User,
                username,
                password,
                role="doctor",
                first_name=first,
                last_name=last,
                email=f"{username}@demo.example.test",
            )
            doctor, _ = DoctorProfile.objects.update_or_create(
                user=user,
                defaults={
                    "specialization": specialty,
                    "hospital": hospitals[hospital_key],
                    "consultation_fee": Decimal(fee),
                    "years_of_experience": experience,
                    "license_number": f"DEMO-{username.upper()}",
                },
            )
            doctor.available_days.set([weekdays[day] for day in days])
            for day in days:
                DoctorAvailability.objects.get_or_create(
                    doctor=doctor,
                    day=day,
                    defaults={"start_time": time(9), "end_time": time(16)},
                )
            doctors[username] = doctor

        patients = {}
        for username, first, last, gender in PATIENTS:
            user = self.get_user(
                User,
                username,
                password,
                role="patient",
                first_name=first,
                last_name=last,
                gender=gender,
                email=f"{username}@demo.example.test",
            )
            patients[username], _ = PatientProfile.objects.get_or_create(user=user)

        for patient, doctor in zip(patients.values(), doctors.values()):
            patient.primary_doctor = doctor
            patient.save(update_fields=["primary_doctor"])
            doctor.patients.add(patient)

        for username, first, last, hospital_key in ADMINISTRATORS:
            user = self.get_user(
                User,
                username,
                password,
                role="admin",
                first_name=first,
                last_name=last,
                email=f"{username}@demo.example.test",
            )
            assignment, created = HospitalAdministrator.objects.get_or_create(
                user=user,
                defaults={"hospital": hospitals[hospital_key]},
            )
            if not created and assignment.hospital_id != hospitals[hospital_key].id:
                raise CommandError(
                    f"{username} is already assigned to a different hospital; "
                    "the existing assignment was not changed."
                )

        self.get_superuser(User, password)

        today = timezone.localdate()
        bookings = (
            ("demo_patient_joy", "demo_doctor_amina", 3, time(9, 30), "pending", "physical"),
            ("demo_patient_peter", "demo_doctor_david", 5, time(10, 30), "confirmed", "virtual"),
            ("demo_patient_nia", "demo_doctor_grace", 8, time(11), "pending", "physical"),
            ("demo_patient_samuel", "demo_doctor_brian", -10, time(13), "completed", "physical"),
            ("demo_patient_leah", "demo_doctor_zawadi", 12, time(14), "confirmed", "virtual"),
        )
        new_appointments = []
        for patient_name, doctor_name, offset, slot, status, appointment_type in bookings:
            doctor = doctors[doctor_name]
            appointment_date = today + timedelta(days=offset)
            existing = Appointment.objects.filter(
                doctor=doctor,
                date=appointment_date,
                time=slot,
                is_active=True,
            ).first()
            if existing:
                continue
            new_appointments.append(
                Appointment(
                    patient=patients[patient_name],
                    doctor=doctor,
                    hospital=doctor.hospital,
                    date=appointment_date,
                    time=slot,
                    status=status,
                    type=appointment_type,
                    notes="Demo appointment",
                )
            )

        Appointment.objects.bulk_create(new_appointments)
        Billing.objects.bulk_create(
            [
                Billing(
                    appointment=appointment,
                    total_fee=appointment.doctor.consultation_fee,
                    payment_method="mpesa",
                    payment_status="pending",
                )
                for appointment in new_appointments
            ]
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data is ready: "
                f"{len(HOSPITALS)} hospitals, {len(DOCTORS)} doctors, "
                f"{len(PATIENTS)} patients, {len(ADMINISTRATORS)} hospital admins, "
                f"1 superadmin, and {len(new_appointments)} new appointments."
            )
        )
        self.stdout.write(
            "Demo usernames use the demo_ prefix. The supplied password is set "
            "only for accounts created by this command; existing account passwords "
            "are never changed."
        )
        self.stderr.write(
            self.style.WARNING(
                "Warning: demo accounts use a shared password. Use only in a local "
                "development database; never use these credentials in production."
            )
        )

    def get_hospital(self, values):
        hospital, created = Hospital.objects.get_or_create(
            name=values["name"],
            defaults={
                "address": values["address"],
                "contact": values["contact"],
                "email": values["email"],
            },
        )
        if not created and (
            hospital.contact != values["contact"]
            or hospital.email != values["email"]
        ):
            raise CommandError(
                f"A hospital named {values['name']} already exists with different "
                "contact details; it was not changed."
            )
        return hospital

    def get_user(self, User, username, password, **defaults):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return User.objects.create_user(
                username=username,
                password=password,
                **defaults,
            )

        if user.role != defaults["role"] or user.is_superuser:
            raise CommandError(
                f"Username {username} already belongs to a different account type; "
                "no account was changed."
            )
        return user

    def get_superuser(self, User, password):
        username = "demo_superadmin"
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return User.objects.create_superuser(
                username=username,
                password=password,
                email="demo_superadmin@demo.example.test",
                first_name="Demo",
                last_name="Superadmin",
                role="admin",
            )

        if not user.is_superuser:
            raise CommandError(
                "Username demo_superadmin already belongs to a non-superuser; "
                "no account was changed."
            )
        return user
