from django.urls import path
from .views import (
    PharmacyItemListCreateView, PharmacyItemDetailView,
    OrderListCreateView, OrderDetailView,
    PaymentListCreateView, PaymentDetailView,
    pharmacy
)
from .payment import MpesaPaymentView
app_name = "pharmacy"

urlpatterns = [
    path("pharmacy/", pharmacy, name="pharmacy"),
    path('pharmacy-items/', PharmacyItemListCreateView.as_view(), name='pharmacy-item-list'),
    path('pharmacy-items/<int:pk>/', PharmacyItemDetailView.as_view(), name='pharmacy-item-detail'),
    
    path('orders/', OrderListCreateView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    
    path('payments/', PaymentListCreateView.as_view(), name='payment-list'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path("mpesa/pay/", MpesaPaymentView.as_view(), name="mpesa-pay"),
]
