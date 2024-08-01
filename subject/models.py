from django.db import models
from accounts.models import CustomUser
# Create your models here.


class Subject(models.Model):
    subject_name = models.CharField(max_length=100)
    assigned_teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    units = models.IntegerField()

    def __str__(self):
        return self.subject_name
    

