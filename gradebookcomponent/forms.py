from django import forms
from .models import GradeBookComponents, TermGradeBookComponents
from subject.models import Subject
from course.models import Term
from django.db.models import Sum
from course.models import Semester
from django.utils import timezone


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
            
    def clean(self):
        cleaned_data = super().clean()
        subject = cleaned_data.get('subject')
        percentage = cleaned_data.get('percentage')

        if subject and percentage:
            # Calculate the total percentage for the subject
            existing_percentage = GradeBookComponents.objects.filter(subject=subject).aggregate(
                total_percentage=Sum('percentage')
            )['total_percentage'] or 0

            total_percentage = existing_percentage + percentage

            if total_percentage > 100:
                raise forms.ValidationError(
                    f"The total percentage for {subject} exceeds 100%. You currently have {existing_percentage}%, and adding this will result in {total_percentage}%."
                )

        return cleaned_data


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
            'percentage': forms.TextInput(attrs={'class': 'form-control'}),

        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TermGradeBookComponentsForm, self).__init__(*args, **kwargs)

        # Get the current semester based on today's date
        today = timezone.now().date()
        current_semester = Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()

        if user and current_semester:
            if user.is_superuser:
                # If the user is an admin, show all terms and subjects within the current semester
                self.fields['term'].queryset = Term.objects.filter(semester=current_semester)
                self.fields['subjects'].queryset = Subject.objects.filter(
                    subjectenrollment__semester=current_semester
                ).distinct()
            else:
                # If the user is not an admin, restrict based on assigned subjects within the current semester
                self.fields['term'].queryset = Term.objects.filter(
                    semester=current_semester,
                    semester__subjectenrollment__subject__assign_teacher=user
                ).distinct()

                if self.data.get('term'):
                    try:
                        term_id = int(self.data.get('term'))
                        term = Term.objects.get(id=term_id, semester=current_semester)
                        self.fields['subjects'].queryset = Subject.objects.filter(
                            subjectenrollment__semester=current_semester,
                            assign_teacher=user
                        ).distinct()
                    except (ValueError, TypeError, Term.DoesNotExist):
                        self.fields['subjects'].queryset = Subject.objects.none()
                else:
                    # Default to showing all subjects assigned to the teacher within the current semester if no term is selected yet
                    self.fields['subjects'].queryset = Subject.objects.filter(
                        subjectenrollment__semester=current_semester,
                        assign_teacher=user
                    ).distinct()


    def clean(self):
        cleaned_data = super().clean()
        term = cleaned_data.get('term')
        percentage = cleaned_data.get('percentage')

        if term and percentage:
            existing_percentage = TermGradeBookComponents.objects.filter(term=term).aggregate(
                total_percentage=Sum('percentage')
            )['total_percentage'] or 0

            total_percentage = existing_percentage + percentage

            if total_percentage > 100:
                raise forms.ValidationError(
                    f"The total percentage for the term '{term.term_name}' exceeds 100%. "
                    f"You currently have {existing_percentage}%, and adding this will result in {total_percentage}%."
                )

        return cleaned_data


