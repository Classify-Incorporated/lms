from django import forms
from .models import Module

class moduleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = '__all__'