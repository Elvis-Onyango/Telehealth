from rest_framework import generics, permissions
from .models import PharmacyItem, Order, Payment
from .serializers import PharmacyItemSerializer, OrderSerializer, PaymentSerializer
from django.shortcuts import render


class PharmacyItemListCreateView(generics.ListCreateAPIView):
    queryset = PharmacyItem.objects.all()
    serializer_class = PharmacyItemSerializer
    permission_classes = [permissions.IsAuthenticated]

class PharmacyItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PharmacyItem.objects.all()
    serializer_class = PharmacyItemSerializer
    permission_classes = [permissions.IsAuthenticated]

class OrderListCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

class PaymentListCreateView(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]



def pharmacy(request):
    items = PharmacyItem.objects.all()
    return render(request, "pharmacy/pharmacy.html", {"items": items})
