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


from django import forms
from .models import DoctorProfile,User,Weekday


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'gender', 'profile_picture']
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': '+1234567890'}),
            'gender': forms.Select(choices=[('', 'Select gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
        }

class DoctorProfileUpdateForm(forms.ModelForm):
    available_days = forms.ModelMultipleChoiceField(
        queryset=Weekday.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'hospital', 'available_days', 'consultation_fee', 
                 'years_of_experience', 'license_number', 'certifications', 'profile_picture']
        widgets = {
            'consultation_fee': forms.NumberInput(attrs={'step': '100'}),
            'years_of_experience': forms.NumberInput(attrs={'min': '2'}),
            'license_number': forms.TextInput(attrs={'placeholder': 'Medical license number'}),
        }

