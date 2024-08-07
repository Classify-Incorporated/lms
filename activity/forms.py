# forms.py
from django import forms
from .models import Activity, ActivityQuestion, QuestionChoice, QuizType

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['activity_name', 'activity_type', 'term', 'start_time', 'end_time']
        widgets = {
            'activity_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter activity name'}),
            'activity_type': forms.Select(attrs={'class': 'form-control'}),
            'term': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class ActivityQuestionForm(forms.ModelForm):
    class Meta:
        model = ActivityQuestion
        fields = ['question_text', 'correct_answer', 'quiz_type', 'score']

class QuestionChoiceForm(forms.ModelForm):
    class Meta:
        model = QuestionChoice
        fields = ['choice_text']
