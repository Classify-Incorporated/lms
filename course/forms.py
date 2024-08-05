from django import forms
from .models import Course

class courseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
        widgets = {
            'course_name': forms.TextInput(attrs={'class': 'form-control'}),
            'subjects': forms.SelectMultiple(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
                'data-actions-box': 'true',
            }),  
        }