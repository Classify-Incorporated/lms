from django.db import models
from accounts.models import CustomUser
# Create your models here.


class Subject(models.Model):
    subject_name = models.CharField(max_length=100)
    assigned_teachers = models.ManyToManyField(CustomUser, blank=True)

    def __str__(self):
        return self.subject_name
    

