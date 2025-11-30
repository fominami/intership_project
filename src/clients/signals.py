from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from clients.models import Client


@receiver(post_save, sender=User)
def create_client_profile(sender, instance, created, **kwargs):
    if created and instance.role == User.Role.CLIENT:
        Client.objects.create(user=instance)
