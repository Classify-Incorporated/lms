from django import forms
from .models import Semester

class semesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = '__all__'
        widgets = {
            'semester_name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.TextInput(attrs={'class': 'form-control'}),
            'end_date': forms.TextInput(attrs={'class': 'form-control'}),
            'school_year': forms.TextInput(attrs={'class': 'form-control'}),
        }