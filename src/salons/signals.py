from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from salons.models import Salon


@receiver(post_save, sender=User)
def create_salon_profile(sender, instance, created, **kwargs):
    if created and instance.role == User.Role.SALON:
        Salon.objects.create(user=instance)
