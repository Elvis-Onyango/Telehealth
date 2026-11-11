from django.contrib.auth.views import LoginView
from django.urls import reverse

class CustomAdminLoginView(LoginView):
    template_name = "admin/login.html"  
    redirect_authenticated_user = False

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return reverse("superadmin-dashboard")
        if user.role == "admin" and hasattr(user, "hospital_administration"):
            return reverse("hospital-dashboard")
        if user.is_staff:
            return reverse("admin:index")
        return "/"
