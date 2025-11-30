from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from suppliers.models import Supplier


@receiver(post_save, sender=User)
def create_supplier_profile(sender, instance, created, **kwargs):
    if created and instance.role == User.Role.SUPPLIER:
        Supplier.objects.create(user=instance)
