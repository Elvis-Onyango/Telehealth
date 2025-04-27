from django.urls import path
from django.contrib.auth import views as auth_views
from .views import CustomAdminLoginView

urlpatterns = [
    path("", CustomAdminLoginView.as_view(), name="custom-admin-login"),
]
