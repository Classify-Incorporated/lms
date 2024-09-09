from django import forms
from .models import Activity, ActivityType
from accounts.models import CustomUser

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = '__all__'
        widgets = {
            'activity_name': forms.TextInput(attrs={'class': 'form-control'}),
            'activity_type': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'term': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'show_score': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'remedial': forms.CheckboxInput(attrs={'class': 'form-check-input'}), 
            'remedial_student': forms.Select(attrs={'class': 'form-control'}),  
        }

    def __init__(self, *args, **kwargs):
        super(ActivityForm, self).__init__(*args, **kwargs)
        self.fields['remedial_student'].queryset = CustomUser.objects.filter(profile__role__name__iexact='Student')

        if not self.instance.remedial:
            self.fields['remedial_student'].widget.attrs['style'] = 'display:none;'

class activityTypeForm(forms.ModelForm):
    class Meta:
        model = ActivityType
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }