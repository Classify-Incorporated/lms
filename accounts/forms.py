from django import forms
from .models import CustomUser, Profile

class CustomLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class profileForm(forms.ModelForm):
    
    class Meta:
        model = Profile
        fields = '__all__'