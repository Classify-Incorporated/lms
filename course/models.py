from django.db import models
from accounts.models import CustomUser
from subject.models import Subject
# Create your models here.

class Course(models.Model):
    course_name = models.CharField(max_length=100)
    subjects = models.ManyToManyField(Subject)

    def __str__(self):
        return self.course_name
    

class SubjectEnrollment(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject)
    enrollment_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} enrolled in subjects"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student'], name='unique_student_subjects')
        ]