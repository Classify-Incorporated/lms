from django import forms
from .models import GradeBookComponents

class GradeBookComponentsForm(forms.ModelForm):
    class Meta:
        model = GradeBookComponents
        fields = '__all__'