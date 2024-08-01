from django import forms
from .models import Role


class roleForm(forms.ModelForm):
    
    class Meta:
        model = Role
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }