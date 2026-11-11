from rest_framework import generics, permissions
from .models import PharmacyItem, Order, Payment
from .serializers import PharmacyItemSerializer, OrderSerializer, PaymentSerializer
from django.shortcuts import render


class PharmacyItemListCreateView(generics.ListCreateAPIView):
    queryset = PharmacyItem.objects.all()
    serializer_class = PharmacyItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAdminUser()]
        return super().get_permissions()


class PharmacyItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PharmacyItem.objects.all()
    serializer_class = PharmacyItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            return [permissions.IsAdminUser()]
        return super().get_permissions()


class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "orderitem_set__pharmacy_item"
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "orderitem_set__pharmacy_item"
        )


class PaymentListCreateView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user).select_related("order")


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user).select_related("order")



def pharmacy(request):
    items = PharmacyItem.objects.all()
    return render(request, "pharmacy/pharmacy.html", {"items": items})
