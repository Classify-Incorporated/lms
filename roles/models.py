from django.db import models
from django.utils import timezone

# Create your models here.
class Role(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            original_role = Role.objects.get(pk=self.pk)
            if self.name != original_role.name or self.description != original_role.description:
                self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name