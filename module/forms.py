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

    def __init__(self, *args, **kwargs):
        super(SCORMPackageForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
