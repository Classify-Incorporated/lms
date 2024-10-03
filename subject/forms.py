from django import forms
from .models import Subject
from accounts.models import CustomUser, Role

class subjectForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(subjectForm, self).__init__(*args, **kwargs)
        teacher_role = Role.objects.get(name__iexact='teacher')
        self.fields['assign_teacher'].queryset = CustomUser.objects.filter(profile__role=teacher_role)
        
        # Remove the default empty option for the term field
        self.fields['assign_teacher'].empty_label = None

    class Meta:
        model = Subject
        fields = '__all__'
        widgets = {
            'subject_name': forms.TextInput(attrs={'class': 'form-control'}),
            'subject_short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'subject_photo': forms.ClearableFileInput(attrs={
                'class': 'custom-file-input',
                'id': 'customFile',
            }),
            'assign_teacher': forms.Select(attrs={
                'class': 'form-control selectpicker',  # Add selectpicker class if needed
                'data-live-search': 'true',  # Optional: Enable live search in selectpicker
                'data-actions-box': 'true',  # Optional: Actions box for select all/deselect
                'title': 'Select Teacher',  # This sets a placeholder-like text without adding an option
                'data-style': 'btn-outline-secondary',
            }),
            'subject_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'subject_code': forms.TextInput(attrs={'class': 'form-control'}),
            'schedule_start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'schedule_end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),

        }
