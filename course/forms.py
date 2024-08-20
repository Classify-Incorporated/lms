from django import forms
from .models import Semester, Term
from subject.models import Subject

class semesterForm(forms.ModelForm):
    school_year = forms.ChoiceField(
        choices=[(r, r) for r in range(1900, 2100)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='School Year'
    )

    class Meta:
        model = Semester
        fields = ['semester_name', 'start_date', 'end_date', 'school_year']
        widgets = {
            'semester_name': forms.Select(attrs={'class': 'form-control'}),  # Use Select widget for dropdown
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

class ParticipationForm(forms.Form):
    term = forms.ModelChoiceField(queryset=Term.objects.all(), label="Select Term")
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), label="Select Subject")
    max_score = forms.DecimalField(max_digits=5, decimal_places=2, label="Max Score", initial=100)

