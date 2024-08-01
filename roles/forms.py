from django import forms
from .models import Role


class roleForm(forms.ModelForm):
    
    class Meta:
        model = Role
        fields = '__all__'