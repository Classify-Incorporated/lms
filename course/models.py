from django.db import models
from accounts.models import CustomUser
from subject.models import Subject
from django.utils import timezone
from django.conf import settings

class SubjectEnrollment(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, null=True, blank=True)
    enrollment_date = models.DateField(auto_now_add=True)
    semester = models.ForeignKey('Semester', on_delete=models.PROTECT, null=True, blank=True)
    can_view_grade = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'subject', 'semester'], name='unique_student_subject_semester')
        ]

    def __str__(self):
        return f"{self.student} enrolled in {self.subject}"

class Retake(models.Model):
    subject_enrollment = models.ForeignKey(SubjectEnrollment, on_delete=models.PROTECT, related_name='retakes')
    retake_date = models.DateField(auto_now_add=True)
    reason = models.TextField()

    

    def __str__(self):
        return f"Retake of {self.subject_enrollment.subject} by {self.subject_enrollment.student} on {self.retake_date}"


class Semester(models.Model):
    SEMESTER_CHOICES = [
        ('First Semester', 'First Semester'),
        ('Second Semester', 'Second Semester'),
    ]
    semester_name = models.CharField(max_length=50, choices=SEMESTER_CHOICES)
    school_year = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    end_semester = models.BooleanField(default=False)
    create_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.end_semester and not self.end_date == timezone.now().date():
            self.end_date = timezone.now().date()

        super(Semester, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.semester_name} ({self.start_date} - {self.end_date}) "
    

class Term(models.Model):
    term_name = models.CharField(max_length=50)
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.term_name} - {self.start_date} - {self.end_date}"

class StudentParticipationScore(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    term = models.ForeignKey(Term, on_delete=models.PROTECT)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)

    class Meta:
        unique_together = ('student', 'subject', 'term')

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.subject.subject_name} - {self.term.term_name} - {self.score}/{self.max_score}"
    

class Attendance(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    date = models.DateField(null=True, blank=True)
    status = models.ForeignKey('AttendanceStatus', on_delete=models.PROTECT, null=True, blank=True) 
    remark = models.TextField(null=True, blank=True)  # Additional remarks for the attendance (optional)

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.subject.subject_name} ({self.status})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'subject', 'date'], name='unique_attendance_per_day')
        ]

class AttendanceStatus(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Late', 'Late'),
        ('Absent', 'Absent'),
        ('Excused', 'Excused'),
    ]
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True)

    def __str__(self):
        return self.status
