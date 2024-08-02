from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from roles.models import Role
import os
import uuid

def get_upload_path(instance, filename):
    filename = f"{uuid.uuid4()}{os.path.splitext(filename)[1]}"
    return os.path.join('profile', filename)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.BooleanField(default=True, null=True, blank=True)
    STATUS_TYPE = [
        ('Regular', 'Regular'),
        ('Irregular', 'Irregular'),
    ]
    student_status = models.CharField(max_length=15, choices=STATUS_TYPE, null=True, blank=True)

    #Personal Information
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    student_photo = models.ImageField(upload_to= get_upload_path, null=True, blank=True)
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    nationality = models.CharField(max_length=255, null=True, blank=True)

    #Contact Information
    address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    #Academic Information
    identification = models.CharField(max_length=255, null=True, blank=True)
    YEAR_LEVEL_CHOICES = [
        ('College 1st Year', 'College 1st Year'),
        ('College 2st Year', 'College 2st Year'),
        ('College 3st Year', 'College 3st Year'),
        ('College 4st Year', 'College 4st Year'),
    ]
    grade_year_level = models.CharField(max_length=255, choices=YEAR_LEVEL_CHOICES, null=True, blank=True)
    major = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.user.email