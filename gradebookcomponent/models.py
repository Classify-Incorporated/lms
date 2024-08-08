from django.db import models
from activity.models import ActivityType
# Create your models here.

class GradeBookComponents(models.Model):
    activity_type = models.ForeignKey(ActivityType, on_delete=models.CASCADE, related_name='gradebook_components', null=True, blank=True)
    category_name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    equivalent = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category_name} ({self.percentage}%)"