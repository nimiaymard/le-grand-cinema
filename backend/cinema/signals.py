
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Billet, Reservation


@receiver(post_save, sender=Reservation)
def creer_billet_automatiquement(sender, instance, **kwargs):
    if instance.statut == Reservation.Statut.CONFIRMEE:
        Billet.objects.get_or_create(
            reservation=instance
        )
