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
            'file': forms.ClearableFileInput(attrs={
                'class': 'custom-file-input',  # Use Bootstrap custom file input class
                'aria-describedby': 'inputGroupFileAddon',  # Add ARIA attributes for accessibility
            }),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'term': forms.Select(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
                'data-actions-box': 'true',
                'data-style': 'btn-outline-secondary',
                'title': 'Select Term'
            }),
            'display_lesson_for_selected_users': forms.SelectMultiple(
                attrs={'class': 'selectpicker form-control', 'data-live-search': 'true', 'data-actions-box': 'true'}
            ),
            'allow_download': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
        }

    display_lesson_for_selected_users = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.filter(profile__role__name__iexact='Student'),
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'selectpicker form-control', 'data-live-search': 'true', 'data-actions-box': 'true', 'data-style': 'btn-outline-secondary'}
        ),
    )

    def __init__(self, *args, **kwargs):
        current_semester = kwargs.pop('current_semester', None)
        super().__init__(*args, **kwargs)

        # Filter terms based on the current semester
        if current_semester:
            self.fields['term'].queryset = Term.objects.filter(semester=current_semester)
        else:
            self.fields['term'].queryset = Term.objects.none()

        # Remove the default empty option for the term field
        self.fields['term'].empty_label = None
