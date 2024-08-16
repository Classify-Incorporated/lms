from django import forms
from .models import Subject
from accounts.models import CustomUser, Role

class subjectForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(subjectForm, self).__init__(*args, **kwargs)
        teacher_role = Role.objects.get(name__iexact='teacher')
        self.fields['assign_teacher'].queryset = CustomUser.objects.filter(profile__role=teacher_role)

    class Meta:
        model = Subject
        fields = '__all__'