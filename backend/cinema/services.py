
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Place, Reservation, ReservationPlace, Seance


class ErreurReservation(Exception):
    """Erreur métier liée à une réservation."""


def obtenir_places_disponibles(seance_id):
    """Retourne les places encore disponibles pour une séance."""

    seance = Seance.objects.select_related("salle").get(pk=seance_id)

    places_occupees = ReservationPlace.objects.filter(
        seance=seance,
        date_liberation__isnull=True,
    ).values_list("place_id", flat=True)

    return Place.objects.filter(
        salle=seance.salle,
        est_active=True,
    ).exclude(
        pk__in=places_occupees
    ).order_by("rangee", "numero")


def creer_reservation(utilisateur, seance_id, place_ids):
    """Réserve plusieurs places dans une transaction atomique."""

    if not utilisateur.is_authenticated:
        raise ErreurReservation("Authentification obligatoire.")

    if not isinstance(place_ids, list) or not place_ids:
        raise ErreurReservation("Sélectionnez au moins une place.")

    if any(type(place_id) is not int or place_id <= 0 for place_id in place_ids):
        raise ErreurReservation("Identifiants de places invalides.")

    if len(place_ids) != len(set(place_ids)):
        raise ErreurReservation("Une place a été sélectionnée plusieurs fois.")

    try:
        with transaction.atomic():
            seance = Seance.objects.select_for_update().get(
                pk=seance_id
            )

            if seance.statut != Seance.Statut.PROGRAMMEE:
                raise ErreurReservation("Cette séance n'est pas réservable.")

            if seance.date_debut <= timezone.now():
                raise ErreurReservation("Cette séance a déjà commencé.")

            if not seance.salle.est_active:
                raise ErreurReservation("Cette salle est indisponible.")

            places = list(
                Place.objects.filter(
                    pk__in=place_ids,
                    salle=seance.salle,
                    est_active=True,
                ).order_by("pk")
            )

            if len(places) != len(place_ids):
                raise ErreurReservation(
                    "Une ou plusieurs places sont invalides."
                )

            places_occupees = ReservationPlace.objects.filter(
                seance=seance,
                place_id__in=place_ids,
                date_liberation__isnull=True,
            ).exists()

            if places_occupees:
                raise ErreurReservation(
                    "Une ou plusieurs places sont déjà réservées."
                )

            montant = seance.prix * Decimal(len(places))

            reservation = Reservation.objects.create(
                utilisateur=utilisateur,
                seance=seance,
                statut=Reservation.Statut.CONFIRMEE,
                montant_total=montant,
            )

            ReservationPlace.objects.bulk_create([
                ReservationPlace(
                    reservation=reservation,
                    seance=seance,
                    salle=seance.salle,
                    place=place,
                )
                for place in places
            ])

            return reservation

    except Seance.DoesNotExist as exc:
        raise ErreurReservation("Séance introuvable.") from exc
    except IntegrityError as exc:
        raise ErreurReservation(
            "Conflit de réservation. Veuillez réessayer."
        ) from exc


def annuler_reservation(reservation_id, utilisateur):
    """Annule une réservation et libère ses places."""

    try:
        with transaction.atomic():
            reservation = (
                Reservation.objects.select_for_update()
                .select_related("seance")
                .get(pk=reservation_id, utilisateur=utilisateur)
            )

            if reservation.statut == Reservation.Statut.ANNULEE:
                raise ErreurReservation(
                    "Cette réservation est déjà annulée."
                )

            if reservation.seance.date_debut <= timezone.now():
                raise ErreurReservation(
                    "Impossible d'annuler une séance déjà commencée."
                )

            reservation.statut = Reservation.Statut.ANNULEE
            reservation.save(update_fields=["statut"])

            ReservationPlace.objects.filter(
                reservation=reservation,
                date_liberation__isnull=True,
            ).update(date_liberation=timezone.now())

            return reservation

    except Reservation.DoesNotExist as exc:
        raise ErreurReservation("Réservation introuvable.") from exc
