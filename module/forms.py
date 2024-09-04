from django import forms
from .models import Module
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from course.models import Term

class moduleForm(forms.ModelForm):
    class Meta:
        model = Module
        exclude = ['subject']
        widgets = {
            'file_name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'term': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hide_lesson_for_student': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hide_lesson_for_selected_users': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    hide_lesson_for_selected_users = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.filter(profile__role__name__iexact='student'),  
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
    )

    start_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        current_semester = kwargs.pop('current_semester', None)  # Get the current semester from the view
        super().__init__(*args, **kwargs)

        # Check if current_semester was passed correctly and if it's valid
        print(f"Current Semester: {current_semester}")

        # Filter terms based on the current semester
        if current_semester:
            self.fields['term'].queryset = Term.objects.filter(semester=current_semester)
            print(f"Terms for current semester: {self.fields['term'].queryset}")
        else:
            self.fields['term'].queryset = Term.objects.none()  # If no semester is passed, no terms are shown
            print("No current semester passed, no terms available.")


