
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import ReservationPlace

logger = logging.getLogger(__name__)


def envoyer_confirmation_reservation(reservation):
    """Envoie un email après confirmation d'une réservation."""

    try:
        seance = reservation.seance
        utilisateur = reservation.utilisateur

        places = ReservationPlace.objects.filter(
            reservation=reservation,
            date_liberation__isnull=True,
        ).select_related("place").order_by(
            "place__rangee",
            "place__numero",
        )

        places_texte = ", ".join(
            f"{rp.place.rangee}{rp.place.numero}"
            for rp in places
        )

        date_seance = timezone.localtime(
            seance.date_debut
        ).strftime("%d/%m/%Y à %H:%M")

        sujet = (
            f"Confirmation de réservation n°{reservation.id}"
            " - Le Grand Cinéma"
        )

        message = f"""Bonjour,

Votre réservation a été confirmée !

Film : {seance.film.titre}
Séance : {date_seance}
Salle : {seance.salle.nom}
Places : {places_texte}
Montant total : {reservation.montant_total} €

Numéro de réservation : {reservation.id}

Merci pour votre confiance.

L'équipe Le Grand Cinéma
"""

        send_mail(
            subject=sujet,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[utilisateur.email],
            fail_silently=False,
        )

    except Exception:
        logger.exception(
            "Échec de l'envoi de l'email pour la réservation %s",
            reservation.id,
        )

def envoyer_confirmation_annulation(reservation):
    """Envoie un email après l'annulation d'une réservation."""

    try:
        seance = reservation.seance
        utilisateur = reservation.utilisateur

        # Conserver les places annulées dans le message,
        # même après leur libération.
        places = (
            ReservationPlace.objects.filter(
                reservation=reservation,
            )
            .select_related("place")
            .order_by("place__rangee", "place__numero")
        )

        places_texte = ", ".join(
            f"{rp.place.rangee}{rp.place.numero}"
            for rp in places
        )

        date_seance = timezone.localtime(
            seance.date_debut
        ).strftime("%d/%m/%Y à %H:%M")

        sujet = (
            f"Annulation de réservation n°{reservation.id}"
            " - Le Grand Cinéma"
        )

        message = f"""Bonjour,

Votre réservation a bien été annulée.

Numéro de réservation : {reservation.id}
Film : {seance.film.titre}
Séance : {date_seance}
Salle : {seance.salle.nom}
Places annulées : {places_texte}

Les places associées à votre réservation ont été libérées
et sont de nouveau disponibles.

Merci de votre compréhension.

L'équipe Le Grand Cinéma
"""

        send_mail(
            subject=sujet,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[utilisateur.email],
            fail_silently=False,
        )

    except Exception:
        logger.exception(
            "Échec de l'email d'annulation pour la réservation %s",
            reservation.id,
        )
