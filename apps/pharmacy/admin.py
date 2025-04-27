from django.contrib import admin
from .models import PharmacyItem, Order, OrderItem, Payment

@admin.register(PharmacyItem)
class PharmacyItemAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock")
    search_fields = ("name",)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_price", "ordered_at")
    list_filter = ("status",)
    search_fields = ("user__username",)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "pharmacy_item", "quantity")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "amount", "transaction_id", "is_successful", "paid_at")
    search_fields = ("transaction_id",)
