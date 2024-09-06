from django.db import models
from accounts.models import CustomUser
from subject.models import Subject

class SubjectEnrollment(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    enrollment_date = models.DateField(auto_now_add=True)
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE, null=True, blank=True)
    can_view_grade = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'subject', 'semester'], name='unique_student_subject_semester')
        ]

    def __str__(self):
        return f"{self.student} enrolled in {self.subject}"

class Retake(models.Model):
    subject_enrollment = models.ForeignKey(SubjectEnrollment, on_delete=models.CASCADE, related_name='retakes')
    retake_date = models.DateField(auto_now_add=True)
    reason = models.TextField()

    def __str__(self):
        return f"Retake of {self.subject_enrollment.subject} by {self.subject_enrollment.student} on {self.retake_date}"


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

class StudentParticipationScore(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)

    class Meta:
        unique_together = ('student', 'subject', 'term')

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.subject.subject_name} - {self.term.term_name} - {self.score}/{self.max_score}"