from django import forms
from .models import Role
from django.contrib.auth.models import Permission

class roleForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    class Meta:
        model = Role
        fields = (
            'name',
            'permissions',
        )
        widgets = {
            'role_name': forms.TextInput(attrs={'class': 'form-control'}),
        }