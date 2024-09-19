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
    
class profileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['user', 'role', 'student_status', 'first_name', 'last_name', 'date_of_birth', 'student_photo', 'gender', 'nationality', 'address', 'phone_number', 'identification', 'grade_year_level', 'course','department']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'student_status': forms.Select(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
                'title': "Select Status"
            }),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'student_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'identification': forms.TextInput(attrs={'class': 'form-control'}),
            'grade_year_level': forms.Select(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
                'title': "Select Grade Year Level"
            }),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(profileForm, self).__init__(*args, **kwargs)
        
        # Ensure no default empty option appears
        self.fields['student_status'].empty_label = None
        self.fields['grade_year_level'].empty_label = None

        # If student_status or grade_year_level are not required fields, ensure no blank option is inserted
        if not self.fields['student_status'].required:
            self.fields['student_status'].choices = [
                (choice[0], choice[1]) for choice in self.fields['student_status'].choices if choice[0]
            ]

        if not self.fields['grade_year_level'].required:
            self.fields['grade_year_level'].choices = [
                (choice[0], choice[1]) for choice in self.fields['grade_year_level'].choices if choice[0]
            ]

