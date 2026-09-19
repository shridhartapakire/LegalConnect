from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AdvocateProfile, ClientProfile, User


@receiver(post_save, sender=User)
def create_primary_profile(sender, instance: User, created: bool, **kwargs) -> None:
    """Create the one permitted primary service profile with the user account."""
    if not created:
        return
    if instance.is_advocate:
        AdvocateProfile.objects.create(user=instance)
    else:
        ClientProfile.objects.create(user=instance)
