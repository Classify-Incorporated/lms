from django import forms
from .models import Module
from django.core.exceptions import ValidationError
from .models import SCORMPackage
class moduleForm(forms.ModelForm):
    class Meta:
        model = Module
        exclude = ['subject']
        widgets = {
            'file_name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file', False)
        if file:
            if file.size > 25 * 1024 * 1024:
                raise ValidationError("The file is too large. The maximum file size allowed is 25MB.")
        return file
    

class SCORMPackageForm(forms.ModelForm):
    class Meta:
        model = SCORMPackage
        fields = ['package_name', 'pptx_link']
        widgets = {
            'package_name': forms.TextInput(attrs={'class': 'form-control'}),
            'pptx_link': forms.FileInput(attrs={'class': 'form-control'}),
        }