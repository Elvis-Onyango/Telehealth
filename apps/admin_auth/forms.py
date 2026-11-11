from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError

from apps.users.models import User


class SuperadminUserCreationForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=(("patient", "Patient"), ("doctor", "Doctor")))
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if get_user_model().objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        password_validation.validate_password(password)
        return password

    def save(self):
        return get_user_model().objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            email=self.cleaned_data["email"],
            role=self.cleaned_data["role"],
        )


class SuperadminUserManagementForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "is_active"]


class NotificationBroadcastForm(forms.Form):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.order_by("username"),
        required=False,
        help_text="Choose one user, or select broadcast to notify everyone.",
    )
    broadcast = forms.BooleanField(required=False, label="Send to all users")
    message = forms.CharField(max_length=255, widget=forms.Textarea(attrs={"rows": 3}))

    def clean(self):
        cleaned_data = super().clean()
        if bool(cleaned_data.get("recipient")) == bool(cleaned_data.get("broadcast")):
            raise forms.ValidationError(
                "Choose one recipient or send to all users, but not both."
            )
        return cleaned_data
