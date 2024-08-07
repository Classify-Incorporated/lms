from django.db import models
from accounts.models import CustomUser
from subject.models import Subject
import os
import uuid
# Create your models here.

class Course(models.Model):
    course_name = models.CharField(max_length=100)
    course_short_name = models.CharField(max_length=10, null=True, blank=True)
    

    def __str__(self):
        return self.course_name

class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    section_name = models.CharField(max_length=100)
    subjects = models.ManyToManyField(Subject)
    assign_teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    

    def __str__(self):
        return self.section_name
    
class SubjectEnrollment(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject)
    enrollment_date = models.DateField(auto_now_add=True)
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.student} enrolled in subjects"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student'], name='unique_student_subjects')
        ]


class Semester(models.Model):
    SEMESTER_CHOICES  = [
        ('1st Semester', '1st Semester'),
        ('2nd Semester', '2nd Semester'),
        ('3rd Semester', '3rd Semester'),
        ('4th Semester', '4th Semester'),
    ]
    semester_name = models.CharField(max_length=50, choices=SEMESTER_CHOICES )
    school_year = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.semester_name} ({self.start_date} - {self.end_date}) - {self.school_year}"
    
class Term(models.Model):
    term_name = models.CharField(max_length=50)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.term_name} - {self.semester}"