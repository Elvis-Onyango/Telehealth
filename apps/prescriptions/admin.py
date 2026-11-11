from django.contrib import admin
from .models import MedicalHistory, Prescription, MedicalReport, SymptomIntake

@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ('patient', 'allergies', 'chronic_diseases', 'past_surgeries', 'family_medical_history')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'allergies', 'chronic_diseases', 'past_surgeries')
    list_filter = ('chronic_diseases',)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment', 'date_issued')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'doctor__user__first_name', 'doctor__user__last_name')
    list_filter = ('date_issued',)


@admin.register(SymptomIntake)
class SymptomIntakeAdmin(admin.ModelAdmin):
    list_display = ('patient', 'appointment', 'severity', 'created_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'primary_symptoms')
    list_filter = ('severity', 'created_at')


@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment', 'date_issued', 'diagnosis')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'doctor__user__first_name', 'doctor__user__last_name', 'diagnosis')
    list_filter = ('date_issued',)
