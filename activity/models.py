from django.db import models
from subject.models import Subject
from accounts.models import CustomUser
from course.models import Term
import uuid
import os
from logs.models import SubjectLog
from module.models import Module

def get_upload_path(instance, filename):
    filename = f"{uuid.uuid4()}{os.path.splitext(filename)[1]}"
    return os.path.join('uploadDocuments', filename)

class ActivityType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class QuizType(models.Model):
    QUIZ_CHOICES = [
        ('Multiple Choice', 'Multiple Choice'),
        ('Essay', 'Essay'),
        ('True/False', 'True/False'),
        ('Fill in the Blank', 'Fill in the Blank'),
        ('Matching', 'Matching'),
        ('Calculated Numeric', 'Calculated Numeric'),
        ('Document', 'Document'),
        ('Participation', 'Participation'),
    ]

    name = models.CharField(max_length=50, choices=QUIZ_CHOICES)

    def __str__(self):
        return self.name
    
class Activity(models.Model):
    activity_name = models.CharField(max_length=100)
    activity_type = models.ForeignKey(ActivityType, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    show_score = models.BooleanField(default=False)
    remedial = models.BooleanField(default=False) 
    remedial_students = models.ManyToManyField(CustomUser, blank=True, limit_choices_to={'profile__role__name__iexact': 'Student'})

    def __str__(self):
        return self.activity_name
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None 
        super().save(*args, **kwargs)
        if is_new:
            SubjectLog.objects.create(
                subject=self.subject,
                message=f"A new activity named '{self.activity_name}' has been created for {self.subject.subject_name}."
            )
    
    
class ActivityQuestion(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    question_text = models.TextField()
    correct_answer = models.TextField()
    quiz_type = models.ForeignKey(QuizType, on_delete=models.CASCADE, null=True, blank=True)
    score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Question for {self.activity.activity_name}"



class QuestionChoice(models.Model):
    question = models.ForeignKey(ActivityQuestion, related_name='choices', on_delete=models.CASCADE)
    choice_text = models.TextField()

    def __str__(self):
        return f"Choice for {self.question.activity.activity_name}"
    

class StudentActivity(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.student.email} - {self.activity.activity_name}"
    

class StudentQuestion(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    activity_question = models.ForeignKey(ActivityQuestion, on_delete=models.CASCADE, null=True, blank=True)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, null=True, blank=True)
    score = models.FloatField(default=0)
    student_answer = models.TextField(null=True, blank=True)
    uploaded_file = models.FileField(upload_to=get_upload_path, null=True, blank=True)
    status = models.BooleanField(default=False)
    submission_time = models.DateTimeField(null=True, blank=True, default=None)
    is_participation = models.BooleanField(default=False)

    def __str__(self):
        if self.activity_question and self.activity_question.activity:
            return f"{self.student.email} - {self.activity_question.activity.activity_name} - {self.activity_question.question_text}"
        return f"{self.student.email} - No activity question available"
    

