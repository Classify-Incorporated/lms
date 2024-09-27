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
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        # Return full name if available, otherwise return the username
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def has_perm(self, perm, obj=None):
        if super().has_perm(perm, obj):
            return True

        if hasattr(self, 'profile') and self.profile.role:
            role_permissions = self.profile.role.permissions.all()
            if role_permissions.filter(codename=perm.split('.')[1]).exists():
                return True
        
        return False

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
        ('1st Year College', '1st Year College'),
        ('2nd Year College', '2nd Year College'),
        ('3rd Year College', '3rd Year College'),
        ('4th Year College', '4th Year College'),
    ]
    grade_year_level = models.CharField(max_length=255, choices=YEAR_LEVEL_CHOICES, null=True, blank=True)
    COURSE_CHOICES = [
        ('BSIT','Bachelor of Science in Information Technology'),
        ('BSIS', 'Bachelor of Science in Information System'),
        ('BSBA', 'Bachelor of Science in Business Administration'),
        ('BSA', 'Bachelor of Science in Accountancy'),
        ('BSCE', 'Bachelor of Science in Civil Engineering'),
        ('BSEE', 'Bachelor of Science in Electrical Engineering'),
        ('BSED', 'Bachelor of Science in Education'),
        ('BSTM', 'Bachelor of Science in Tourism Management'),
        ('BSHM', 'Bachelor of Science in Hospitality Management'),
        ('BSCS', 'Bachelor of Science in Computer Science'),
        ('BSComE', 'Bachelor of Science in Computer Engineering'),
    ]
    course = models.CharField(max_length=255, choices=COURSE_CHOICES, null=True, blank=True)
    DEPARTMENT_CHOICES = [
        ('Registrar', 'Registrar'),
        ('Admin', 'Admin'),
        ('HR', 'Human Resource'),
    ]
    department = models.CharField(max_length=255, choices=DEPARTMENT_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"