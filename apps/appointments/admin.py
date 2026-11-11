from django.contrib import admin
from .models import Hospital, HospitalAdministrator, Appointment, Billing

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("name", "contact", "email")
    search_fields = ("name", "contact", "email")
    list_filter = ("name",)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(HospitalAdministrator)
class HospitalAdministratorAdmin(admin.ModelAdmin):
    list_display = ("user", "hospital", "created_at")
    list_filter = ("hospital",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "hospital__name")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "date", "time", "status", "created_at")
    list_filter = ("status", "date", "doctor")
    search_fields = ("patient__username", "doctor__user__username", "hospital__name")
    ordering = ("-created_at",)

    def save_model(self, request, obj, form, change):
        if obj.status == "cancelled":
            obj.is_active = False
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ("appointment", "total_fee", "is_paid", "payment_method", "payment_date")
    list_filter = ("payment_status", "payment_method")
    search_fields = ("appointment__patient__user__username", "appointment__doctor__user__username")

    @admin.display(boolean=True, ordering="payment_status", description="Paid")
    def is_paid(self, obj):
        return obj.payment_status == "paid"

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
