from django import forms
from .models import GradeBookComponents, TermGradeBookComponents
from subject.models import Subject
from course.models import Term

class GradeBookComponentsForm(forms.ModelForm):
    class Meta:
        model = GradeBookComponents
        fields = ['subject', 'activity_type', 'category_name', 'percentage', 'is_participation']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'activity_type': forms.Select(attrs={'class': 'form-control'}),
            'category_name': forms.TextInput(attrs={'class': 'form-control'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_participation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(GradeBookComponentsForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['subject'].queryset = Subject.objects.filter(assign_teacher=user)
        if self.instance and self.instance.is_participation:
            self.fields['activity_type'].widget = forms.HiddenInput()

class CopyGradeBookForm(forms.Form):
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),
        label="Target Subject",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    copy_from_subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),
        label="Copy GradeBook from",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CopyGradeBookForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['subject'].queryset = Subject.objects.filter(assign_teacher=user)
            self.fields['copy_from_subject'].queryset = Subject.objects.filter(
                assign_teacher=user,
                gradebook_components__isnull=False
            ).distinct()

class TermGradeBookComponentsForm(forms.ModelForm):
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control selectpicker',
            'data-actions-box': 'true',
            'data-live-search': 'true',  # optional: adds a search box
        }),
        required=True
    )

    class Meta:
        model = TermGradeBookComponents
        fields = ['term', 'subjects', 'percentage']
        widgets = {
            'term': forms.Select(attrs={'class': 'form-control'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TermGradeBookComponentsForm, self).__init__(*args, **kwargs)

        if user:
            self.fields['term'].queryset = Term.objects.filter(
                semester__subjectenrollment__subject__assign_teacher=user
            ).distinct()

            if 'term' in self.data:
                try:
                    term_id = int(self.data.get('term'))
                    term = Term.objects.get(id=term_id)
                    semester = term.semester
                    self.fields['subjects'].queryset = Subject.objects.filter(
                        subjectenrollment__semester=semester,
                        assign_teacher=user
                    ).distinct()
                except (ValueError, TypeError, Term.DoesNotExist):
                    self.fields['subjects'].queryset = Subject.objects.none()
            else:
                self.fields['subjects'].queryset = Subject.objects.filter(
                    assign_teacher=user
                ).distinct()
