from django import forms
from .models import CustomUser, Profile

class CustomLoginForm(forms.Form):
    username = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Password'})
    )
# Profile Form
class profileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['user', 'role', 'student_status', 'first_name', 'last_name', 'date_of_birth', 'student_photo', 'gender', 'nationality', 'address', 'phone_number', 'identification', 'grade_year_level', 'major']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'student_status': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'student_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'identification': forms.TextInput(attrs={'class': 'form-control'}),
            'grade_year_level': forms.Select(attrs={'class': 'form-control'}),
            'major': forms.TextInput(attrs={'class': 'form-control'}),
        }
