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
            'url': forms.URLInput(attrs={'class': 'form-control','placeholder':'Optional'}),
            'term': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hide_lesson_for_student': forms.CheckboxInput(attrs={'class': 'form-check-input'}),  # Added class 'form-check-input' for checkbox
            'allow_download': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hide_lesson_for_selected_users': forms.SelectMultiple(attrs={'class': 'form-control selectpicker', 'data-live-search': 'true', 'data-actions-box': 'true'}),
        }

    hide_lesson_for_selected_users = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.filter(profile__role__name__iexact='student'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control selectpicker', 'data-live-search': 'true', 'data-actions-box': 'true', 'data-style': 'btn-outline-secondary'}),
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
        current_semester = kwargs.pop('current_semester', None)
        super().__init__(*args, **kwargs)

        # Filter terms based on the current semester
        if current_semester:
            self.fields['term'].queryset = Term.objects.filter(semester=current_semester)
        else:
            self.fields['term'].queryset = Term.objects.none()  # If no semester is passed, no terms are shown