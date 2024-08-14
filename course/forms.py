from django import forms
from .models import Semester, Term

class semesterForm(forms.ModelForm):
    school_year = forms.ChoiceField(
        choices=[(r, r) for r in range(1900, 2100)],  # Generates year choices from 2000 to 2050
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='School Year'
    )

    class Meta:
        model = Semester
        fields = ['semester_name', 'start_date', 'end_date', 'school_year']  # Specify fields explicitly
        widgets = {
            'semester_name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
class termForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = '__all__'
        widgets = {
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'term_name': forms.TextInput(attrs={'class': 'form-control'}),
        }