from django import forms
from .models import Semester, Term, Attendance
from subject.models import Subject
from accounts.models import CustomUser
from activity.models import *
import datetime

class semesterForm(forms.ModelForm):
    current_year = datetime.date.today().year
    year_range = range(current_year, current_year + 10) 

    school_year = forms.ChoiceField(
        choices=[(r, r) for r in year_range],

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
                'title': 'Select Semester',
                'required': 'true', 
            }),
            'term_name': forms.Select(attrs={'class': 'form-control', 'required': 'true', }),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': 'true', }),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': 'true', }),
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

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'status', 'remark', 'date']
        widgets = {
            'student': forms.SelectMultiple(
                attrs={'class': 'selectpicker form-control',
                       'data-live-search': 'true',
                       'data-actions-box': 'true',
                       'data-style': 'btn-outline-secondary',
                       'title': 'Select a student',}
            ),
            'status': forms.RadioSelect(),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        current_semester = kwargs.pop('current_semester', None)
        subject = kwargs.pop('subject', None)
        super().__init__(*args, **kwargs)

        if subject and current_semester:
            enrolled_students = CustomUser.objects.filter(
                subjectenrollment__subject=subject,
                subjectenrollment__semester=current_semester,
                profile__role__name__iexact='Student'
            ).distinct()
            self.fields['student'].queryset = enrolled_students
        else:
            self.fields['student'].queryset = CustomUser.objects.none()


class updateAttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['status', 'remark', 'date']  # Exclude the 'student' field
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),  # Use a dropdown for status
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

