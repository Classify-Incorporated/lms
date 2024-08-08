from django.db import models
from subject.models import Subject
from accounts.models import CustomUser
from course.models import Term


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
    ]

    name = models.CharField(max_length=50, choices=QUIZ_CHOICES)

    def __str__(self):
        return self.name
    
class Activity(models.Model):
    activity_name = models.CharField(max_length=100)
    activity_type = models.ForeignKey(ActivityType, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.activity_name
    
    
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
    activity_question = models.ForeignKey(ActivityQuestion, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    student_answer = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=False)
    submission_time = models.DateTimeField(null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.student.email} - {self.activity_question.activity.activity_name} - {self.activity_question.question_text}"