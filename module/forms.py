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
        fields = ['package_name', 'file']
        widgets = {
            'package_name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            file_type = file.content_type.split('/')[0]
            if file.size > 25 * 1024 * 1024:
                raise ValidationError('File size must be under 25MB.')

            valid_mime_types = [
                'application/pdf',
                'image/jpeg',
                'image/png',
                'video/mp4',
            ]
            if file.content_type not in valid_mime_types:
                raise ValidationError('File type not supported. Please upload a PDF, image, or video file.')

        return file
