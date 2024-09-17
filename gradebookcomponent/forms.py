from django import forms
from .models import GradeBookComponents, TermGradeBookComponents, SubGradeBook
from subject.models import Subject
from course.models import Term
from django.db.models import Sum
from course.models import Semester, SubjectEnrollment
from django.utils import timezone
from datetime import date

class GradeBookComponentsForm(forms.ModelForm):
    class Meta:
        model = GradeBookComponents
        fields = ['subject', 'activity_type', 'category_name', 'percentage', 'is_participation']
        widgets = {
            'subject': forms.Select(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
                'data-actions-box': 'true',
                'data-style': 'btn-outline-secondary',
                'title': 'Select Term'}),
            'activity_type': forms.Select(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
                'data-actions-box': 'true',
                'data-style': 'btn-outline-secondary',
                'title': 'Select Term'}),
            'category_name': forms.TextInput(attrs={'class': 'form-control'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_participation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(GradeBookComponentsForm, self).__init__(*args, **kwargs)

        # Get the current date
        today = date.today()
        
        # Remove the default empty option for the term field
        self.fields['subject'].empty_label = None
        
        # Remove the default empty option for the term field
        self.fields['activity_type'].empty_label = None

        # Find the current semester based on today's date
        current_semester = Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()

        if user and current_semester:
            # Filter subjects by the current semester and teacher
            self.fields['subject'].queryset = Subject.objects.filter(
                assign_teacher=user,
                id__in=SubjectEnrollment.objects.filter(
                    semester=current_semester
                ).values_list('subject_id', flat=True)
            )
        
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
    

class SubGradeBookForm(forms.ModelForm):
    class Meta:
        model = SubGradeBook
        fields = ['gradebook', 'category_name', 'percentage']
        widgets = {
            'gradebook': forms.Select(attrs={'class': 'form-control'}),
            'category_name': forms.TextInput(attrs={'class': 'form-control'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(SubGradeBookForm, self).__init__(*args, **kwargs)

        today = date.today()

        current_semester = Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()

        if user and current_semester:
            assigned_subjects = Subject.objects.filter(assign_teacher=user)

            subjects_in_semester = assigned_subjects.filter(
                id__in=SubjectEnrollment.objects.filter(semester=current_semester).values_list('subject_id', flat=True)
            )

            gradebook_queryset = GradeBookComponents.objects.filter(
                teacher=user,
                subject__in=subjects_in_semester  
            )

            self.fields['gradebook'].queryset = gradebook_queryset
        


class CopyGradeBookForm(forms.Form):
    subject = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        label="Target Subject(s)",
        widget=forms.SelectMultiple(attrs={'class': 'form-control selectpicker',
                'data-live-search': 'true',
                'data-actions-box': 'true',
                'data-style': 'btn-outline-secondary',
                'title': 'Select Subject'})
    )
    copy_from_subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),
        label="Copy GradeBook from",
        widget=forms.Select(attrs={'class': 'form-control selectpicker',
                'data-live-search': 'true',
                'data-actions-box': 'true',
                'data-style': 'btn-outline-secondary',
                'title': 'Copy From'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CopyGradeBookForm, self).__init__(*args, **kwargs)

        # Get the current date
        today = date.today()
        
        # Remove the default empty option for the term field
        self.fields['subject'].empty_label = None
        
        self.fields['copy_from_subject'].empty_label = None

        # Find the current semester based on today's date
        current_semester = Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()

        if user and current_semester:
            # Check if the user has a profile and a valid role (Teacher or teacher)
            if hasattr(user, 'profile') and user.profile.role and user.profile.role.name.lower() == 'teacher':
                # Filter subjects by the current semester and teacher
                self.fields['subject'].queryset = Subject.objects.filter(
                    assign_teacher=user,
                    id__in=SubjectEnrollment.objects.filter(
                        semester=current_semester
                    ).values_list('subject_id', flat=True)
                )
                self.fields['copy_from_subject'].queryset = Subject.objects.filter(
                    assign_teacher=user,
                    id__in=SubjectEnrollment.objects.filter(
                        semester=current_semester,
                        subject__gradebook_components__isnull=False
                    ).values_list('subject_id', flat=True)
                ).distinct()
            else:
                # For admin or other users, display all subjects within the current semester
                self.fields['subject'].queryset = Subject.objects.filter(
                    id__in=SubjectEnrollment.objects.filter(
                        semester=current_semester
                    ).values_list('subject_id', flat=True)
                )
                self.fields['copy_from_subject'].queryset = Subject.objects.filter(
                    id__in=SubjectEnrollment.objects.filter(
                        semester=current_semester,
                        subject__gradebook_components__isnull=False
                    ).values_list('subject_id', flat=True)
                ).distinct()
        else:
            # If no current semester is found, don't show any subjects
            self.fields['subject'].queryset = Subject.objects.none()
            self.fields['copy_from_subject'].queryset = Subject.objects.none()


class TermGradeBookComponentsForm(forms.ModelForm):
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control selectpicker',
            'data-actions-box': 'true',
            'data-live-search': 'true',  # optional: adds a search box
            'title': 'Select Subject',
        }),
        required=True
    )

    class Meta:
        model = TermGradeBookComponents
        fields = ['term', 'subjects', 'percentage']
        widgets = {
            'term': forms.Select(attrs={
                'class': 'form-control selectpicker',
                'data-actions-box': 'true',
                'data-live-search': 'true',  # optional: adds a search box
                'title': 'Select Term',
            }),
            'percentage': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TermGradeBookComponentsForm, self).__init__(*args, **kwargs)

        # Add a placeholder or title to the Select field
        self.fields['term'].empty_label = None

        # Get the current semester based on today's date
        today = timezone.now().date()
        current_semester = Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()

        if user and current_semester:
            if user.is_superuser:
                # Admin users can see all terms and subjects in the current semester
                self.fields['term'].queryset = Term.objects.filter(semester=current_semester)
                self.fields['subjects'].queryset = Subject.objects.filter(
                    subjectenrollment__semester=current_semester
                ).distinct()
            else:
                # For teachers, only show terms and subjects assigned to them in the current semester
                self.fields['term'].queryset = Term.objects.filter(semester=current_semester)

                if self.data.get('term'):
                    # When a term is selected, filter subjects based on the selected term and teacher
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
                    # Default to showing all subjects assigned to the teacher in the current semester if no term is selected
                    self.fields['subjects'].queryset = Subject.objects.filter(
                        subjectenrollment__semester=current_semester,
                        assign_teacher=user
                    ).distinct()

    def clean(self):
        cleaned_data = super().clean()
        term = cleaned_data.get('term')
        percentage = cleaned_data.get('percentage')

        if term and percentage:
            # Get the total percentage already assigned to this term
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