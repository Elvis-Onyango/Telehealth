from django.contrib import admin
from .models import Hospital, Appointment, Billing

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("name", "contact", "email")
    search_fields = ("name", "contact", "email")
    list_filter = ("name",)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "date", "time", "status", "created_at")
    list_filter = ("status", "date", "doctor")
    search_fields = ("patient__username", "doctor__user__username", "hospital__name")
    ordering = ("-created_at",)
    list_editable = ("status",)


@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ("appointment", "total_fee", "is_paid", "payment_method", "payment_date")
    list_filter = ("payment_status", "payment_method")
    search_fields = ("appointment__patient__user__username", "appointment__doctor__user__username")

    @admin.display(boolean=True, ordering="payment_status", description="Paid")
    def is_paid(self, obj):
        return obj.payment_status == "paid"

