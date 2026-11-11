from django.shortcuts import render

from apps.users.models import DoctorProfile

# Create your views here.

def landing_page(request):
    doctors = (
        DoctorProfile.objects.filter(user__is_active=True)
        .select_related("user", "hospital")
        .order_by("user__first_name", "user__last_name")
    )
    specialties = list(
        DoctorProfile.objects.filter(user__is_active=True)
        .exclude(specialization="")
        .order_by("specialization")
        .values_list("specialization", flat=True)
        .distinct()[:8]
    )
    return render(
        request,
        "landing/index.html",
        {
            "doctor_count": doctors.count(),
            "featured_doctors": doctors[:3],
            "specialties": specialties,
        },
    )


def api_testing(request):
    return render(request, "landing/test.html")