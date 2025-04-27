from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

class CustomAdminLoginView(LoginView):
    template_name = "admin/login.html"  
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("admin:index")  # Redirect to Django Admin panel after login
