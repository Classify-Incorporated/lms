from django import forms
from .models import Semester, Term
from subject.models import Subject
from activity.models import Activity

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
            'semester_name': forms.Select(attrs={'class': 'form-control'}), 
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class termForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['semester', 'term_name', 'start_date', 'end_date']
        widgets = {
            'semester': forms.Select(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
                'data-actions-box': 'true',
                'data-style': 'btn-outline-secondary',
                'title': 'Select Semester'
            }),
            'term_name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(termForm, self).__init__(*args, **kwargs)
        
        # Add a placeholder or title to the Select field
        self.fields['semester'].empty_label = None

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        # Validation to check if start_date is before end_date
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("The start date cannot be later than the end date.")

        return cleaned_data


class ParticipationForm(forms.Form):
    term = forms.ModelChoiceField(
        queryset=Term.objects.all(),
        label="Select Term",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        label="Select Subject",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    max_score = forms.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        label="Max Score", 
        initial=100,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
