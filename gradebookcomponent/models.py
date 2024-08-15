from django.db import models
from activity.models import ActivityType
from accounts.models import CustomUser
from subject.models import Subject
from course.models import Term
# Create your models here.

class GradeBookComponents(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='gradebook_components', null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='gradebook_components', null=True, blank=True)
    activity_type = models.ForeignKey(ActivityType, on_delete=models.CASCADE, related_name='gradebook_components', null=True, blank=True)
    category_name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category_name} ({self.percentage}%)"
    

class TermGradeBookComponents(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='term_gradebook_components', null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='term_gradebook_components')
    subjects = models.ManyToManyField(Subject, related_name='term_gradebook_components')
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.term.term_name} ({self.percentage}%)"