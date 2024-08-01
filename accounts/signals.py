from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance, defaults={'first_name': instance.first_name, 'last_name': instance.last_name})
    else:
        profile, created = Profile.objects.get_or_create(user=instance)
        profile.first_name = instance.first_name
        profile.last_name = instance.last_name
        profile.save()
