from django import forms
from .models import Course, Section

class courseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
        widgets = {
            'course_name': forms.TextInput(attrs={'class': 'form-control'}),
            'course_short_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class sectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = '__all__'
        widgets = {
            'course': forms.TextInput(attrs={'class': 'form-control'}),
            'section_name': forms.TextInput(attrs={'class': 'form-control'}),
            'subjects': forms.SelectMultiple(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
                'data-actions-box': 'true',
            }), 
            'assign_teacher': forms.SelectMultiple(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
                'data-actions-box': 'true',
            }),  
        }