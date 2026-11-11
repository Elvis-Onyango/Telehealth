import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.admin_auth.models import AuditEvent
from apps.appointments.models import Appointment, Hospital, HospitalAdministrator

from .models import MedicalHistory, MedicalReport, Prescription, SymptomIntake


User = get_user_model()


class MedicalRecordAccessTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username="records-doctor",
            password="test-pass",
            role="doctor",
        )
        self.patient = User.objects.create_user(
            username="records-patient",
            password="test-pass",
            role="patient",
        )
        self.other_patient = User.objects.create_user(
            username="unrelated-patient",
            password="test-pass",
            role="patient",
        )
        self.doctor_profile = self.doctor.doctor_profile
        self.patient_profile = self.patient.patient_profile
        self.doctor_profile.patients.add(self.patient_profile)
        self.history = MedicalHistory.objects.create(
            patient=self.patient_profile,
            allergies="Pollen",
        )
        self.prescription = Prescription.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            encrypted_prescription="encrypted prescription",
        )
        self.report = MedicalReport.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            diagnosis="Encrypted diagnosis",
        )
        self.client = APIClient()

    def test_patients_cannot_read_other_patients_medical_history(self):
        self.client.force_authenticate(user=self.other_patient)

        list_response = self.client.get(reverse("medical-history-list"))
        detail_response = self.client.get(
            reverse("medical-history-detail", args=[self.history.pk])
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data, [])
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_assigned_doctor_and_patient_can_read_medical_history(self):
        self.client.force_authenticate(user=self.patient)
        patient_response = self.client.get(reverse("medical-history-list"))
        self.client.force_authenticate(user=self.doctor)
        doctor_response = self.client.get(reverse("medical-history-list"))

        self.assertEqual(patient_response.status_code, status.HTTP_200_OK)
        self.assertEqual(doctor_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(patient_response.data), 1)
        self.assertEqual(len(doctor_response.data), 1)

    def test_patient_can_only_create_their_own_medical_history(self):
        self.client.force_authenticate(user=self.other_patient)

        response = self.client.post(
            reverse("medical-history-list"),
            {
                "patient": self.patient_profile.pk,
                "allergies": "Latex",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_history = MedicalHistory.objects.get(patient=self.other_patient.patient_profile)
        self.assertEqual(created_history.allergies, "Latex")

    def test_prescription_access_is_limited_to_patient_and_issuing_doctor(self):
        self.client.force_authenticate(user=self.other_patient)

        response = self.client.get(
            reverse("prescription-detail", args=[self.prescription.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_only_doctors_can_create_prescriptions_and_only_for_care_patients(self):
        self.client.force_authenticate(user=self.other_patient)
        patient_response = self.client.post(
            reverse("prescription-list"),
            {
                "patient": self.patient_profile.pk,
                "encrypted_prescription": "prescription data",
            },
            format="json",
        )
        self.assertEqual(patient_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.doctor)
        response = self.client.post(
            reverse("prescription-list"),
            {
                "patient": self.patient_profile.pk,
                "encrypted_prescription": "prescription data",
                "doctor": self.other_patient.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Prescription.objects.latest("pk")
        self.assertEqual(created.doctor, self.doctor_profile)
        self.assertEqual(created.patient, self.patient_profile)

        denied_response = self.client.post(
            reverse("prescription-list"),
            {
                "patient": self.other_patient.patient_profile.pk,
                "encrypted_prescription": "prescription data",
            },
            format="json",
        )
        self.assertEqual(denied_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_medical_report_access_is_limited_to_patient_and_issuing_doctor(self):
        self.client.force_authenticate(user=self.other_patient)

        response = self.client.get(
            reverse("medical-report-detail", args=[self.report.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_medical_report_file_download_is_private_to_the_care_team(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                report = MedicalReport.objects.create(
                    patient=self.patient_profile,
                    doctor=self.doctor_profile,
                    report_file=SimpleUploadedFile(
                        "lab-report.pdf",
                        b"private report",
                        content_type="application/pdf",
                    ),
                )
                self.client.force_authenticate(user=self.patient)
                report_list_response = self.client.get(reverse("medical-report-list"))
                report_data = next(
                    item
                    for item in report_list_response.data
                    if item["id"] == report.pk
                )
                self.assertTrue(
                    report_data["report_file"],
                )
                self.assertIn(
                    f"/api/prescriptions/medical-reports/{report.pk}/file/",
                    report_data["report_file"],
                )

                self.client.force_authenticate(user=self.doctor)
                response = self.client.get(
                    reverse("medical-report-download", args=[report.pk])
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(b"".join(response.streaming_content), b"private report")

                self.client.force_authenticate(user=self.other_patient)
                denied_response = self.client.get(
                    reverse("medical-report-download", args=[report.pk])
                )
                self.assertEqual(
                    denied_response.status_code,
                    status.HTTP_404_NOT_FOUND,
                )

    def test_hospital_admin_can_view_and_download_only_its_hospital_reports(self):
        hospital = Hospital.objects.create(
            name="Records Hospital",
            address="1 Main Street",
            contact="555-0401",
        )
        self.doctor_profile.hospital = hospital
        self.doctor_profile.save(update_fields=["hospital"])
        report = MedicalReport.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            report_file=SimpleUploadedFile(
                "hospital-lab.pdf",
                b"hospital lab result",
                content_type="application/pdf",
            ),
        )
        unrelated_report = MedicalReport.objects.create(
            patient=self.other_patient.patient_profile,
            doctor=self.doctor_profile,
            diagnosis="Unrelated finding",
        )
        hospital_admin = User.objects.create_user(
            username="records-hospital-admin",
            password="Safe-Password-729!",
            role="admin",
        )
        HospitalAdministrator.objects.create(
            user=hospital_admin,
            hospital=hospital,
        )
        self.client.force_authenticate(user=hospital_admin)

        list_response = self.client.get(reverse("medical-report-list"))
        detail_response = self.client.get(
            reverse("medical-report-detail", args=[report.pk])
        )
        download_response = self.client.get(
            reverse("medical-report-download", args=[report.pk])
        )
        unrelated_response = self.client.get(
            reverse("medical-report-detail", args=[unrelated_report.pk])
        )
        create_response = self.client.post(
            reverse("medical-report-list"),
            {"patient": self.patient_profile.pk, "diagnosis": "Admin report"},
            format="json",
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(
            [entry["id"] for entry in list_response.data],
            [self.report.pk, report.pk],
        )
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(download_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            b"".join(download_response.streaming_content),
            b"hospital lab result",
        )
        self.assertEqual(unrelated_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            AuditEvent.objects.filter(
                actor=hospital_admin,
                action="downloaded_medical_report",
                object_id=str(report.pk),
            ).exists()
        )

    def test_doctor_can_add_lab_results_from_dashboard_linked_form(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.client.force_login(self.doctor)
                response = self.client.post(
                    reverse("medical-report-create-page"),
                    {
                        "patient": self.patient_profile.pk,
                        "diagnosis": "Blood test result",
                        "treatment_plan": "Follow up in one week",
                        "encrypted_notes": "Reviewed by clinician",
                        "report_file": SimpleUploadedFile(
                            "blood-test.pdf",
                            b"test result",
                            content_type="application/pdf",
                        ),
                    },
                    format="multipart",
                )

                self.assertEqual(response.status_code, 302)
                self.assertRedirects(response, reverse("users:doctor-dashboard"))
                report = MedicalReport.objects.latest("pk")
                self.assertEqual(report.doctor, self.doctor_profile)
                self.assertEqual(report.patient, self.patient_profile)
                self.assertEqual(report.get_decrypted_diagnosis(), "Blood test result")
                self.assertTrue(report.report_file)
                self.assertTrue(
                    AuditEvent.objects.filter(
                        actor=self.doctor,
                        action="created_medical_report",
                        object_id=str(report.pk),
                    ).exists()
                )

        self.client.force_login(self.patient)
        denied_response = self.client.get(reverse("medical-report-create-page"))
        self.assertEqual(denied_response.status_code, status.HTTP_403_FORBIDDEN)


class SymptomIntakeAndSummaryTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username="summary-doctor",
            password="test-pass",
            role="doctor",
        )
        self.patient = User.objects.create_user(
            username="summary-patient",
            password="test-pass",
            role="patient",
        )
        self.doctor_profile = self.doctor.doctor_profile
        self.patient_profile = self.patient.patient_profile
        self.doctor_profile.patients.add(self.patient_profile)
        self.appointment = Appointment.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            date="2026-11-12",
            time="10:00:00",
            status="confirmed",
        )

    def test_patient_can_submit_symptom_intake_before_visit(self):
        self.client.force_login(self.patient)

        response = self.client.post(
            reverse("symptom-intake-page", args=[self.appointment.pk]),
            {
                "primary_symptoms": "Fever and cough",
                "symptom_duration": "3 days",
                "severity": "moderate",
                "associated_factors": "worse at night",
                "notes": "Feels tired",
            },
        )

        self.assertEqual(response.status_code, 302)
        intake = SymptomIntake.objects.get(appointment=self.appointment)
        self.assertEqual(intake.primary_symptoms, "Fever and cough")
        self.assertEqual(intake.severity, "moderate")

    def test_visit_summary_pdf_download_contains_summary_details(self):
        intake = SymptomIntake.objects.create(
            patient=self.patient_profile,
            appointment=self.appointment,
            primary_symptoms="Chest pain",
            symptom_duration="2 days",
            severity="severe",
            associated_factors="After exercise",
            notes="Concerned about persistent pain",
        )
        report = MedicalReport.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            appointment=self.appointment,
            diagnosis="Suspected viral infection",
            treatment_plan="Rest and fluids",
            encrypted_notes="Follow-up in 4 days",
        )

        self.client.force_login(self.patient)
        response = self.client.get(
            reverse("visit-summary-download", args=[self.appointment.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pdf_bytes = response.content
        self.assertIn(b"Telehealth Visit Summary", pdf_bytes)
        self.assertIn(b"Chest pain", pdf_bytes)
        self.assertIn(b"Suspected viral infection", pdf_bytes)
        self.assertEqual(response["Content-Type"], "application/pdf")
