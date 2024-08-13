from django import forms
from .models import Semester, Term

class semesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = '__all__'
        widgets = {
            'semester_name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control'}),
            'school_year': forms.TextInput(attrs={'class': 'form-control'}),
        }

class termForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = '__all__'
        widgets = {
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'term_name': forms.TextInput(attrs={'class': 'form-control'}),
        }