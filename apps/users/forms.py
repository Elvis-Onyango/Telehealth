from django import forms
from allauth.account.forms import SignupForm,LoginForm



class CustomSignupForm(SignupForm):
    full_name = forms.CharField(max_length=50, required=True, label="Full Name")

    def save(self, request):
        user = super().save(request)
        user.full_name = self.cleaned_data["full_name"]
        user.save()
        return user



class CustomLoginForm(LoginForm):
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number")

    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get("phone_number")
        # Add custom validation for phone number if needed
        return cleaned_data
