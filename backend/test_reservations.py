
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from cinema.models import (
    Film,
    Place,
    Reservation,
    ReservationPlace,
    Salle,
    Seance,
    Utilisateur,
)


debut = timezone.make_aware(
    datetime(2026, 12, 10, 14, 0)
)

with transaction.atomic():
    film = Film.objects.create(
        titre="Film test réservations",
        duree_minutes=120,
    )

    salle_1 = Salle.objects.create(
        nom="Salle Test Réservation A",
        capacite=20,
    )

    salle_2 = Salle.objects.create(
        nom="Salle Test Réservation B",
        capacite=20,
    )

    place_1 = Place.objects.create(
        salle=salle_1,
        rangee="A",
        numero=1,
    )

    place_autre_salle = Place.objects.create(
        salle=salle_2,
        rangee="A",
        numero=1,
    )

    seance = Seance.objects.create(
        film=film,
        salle=salle_1,
        date_debut=debut,
        date_fin=debut + timedelta(hours=2),
        prix=Decimal("10.00"),
    )

    utilisateur_1 = Utilisateur.objects.create_user(
        email="test.reservation1@example.com",
        password="TestTemporaire123!",
    )

    utilisateur_2 = Utilisateur.objects.create_user(
        email="test.reservation2@example.com",
        password="TestTemporaire123!",
    )

    reservation_1 = Reservation.objects.create(
        utilisateur=utilisateur_1,
        seance=seance,
        montant_total=Decimal("10.00"),
    )

    reservation_2 = Reservation.objects.create(
        utilisateur=utilisateur_2,
        seance=seance,
        montant_total=Decimal("10.00"),
    )

    attribution_1 = ReservationPlace.objects.create(
        reservation=reservation_1,
        seance=seance,
        salle=salle_1,
        place=place_1,
    )

    print("TEST 1 : première réservation autorisée - OK")

    try:
        with transaction.atomic():
            ReservationPlace.objects.create(
                reservation=reservation_2,
                seance=seance,
                salle=salle_1,
                place=place_1,
            )
    except IntegrityError:
        print("TEST 2 : double réservation refusée - OK")
    else:
        raise AssertionError(
            "ERREUR : double réservation autorisée"
        )

    attribution_1.date_liberation = timezone.now()
    attribution_1.save(update_fields=["date_liberation"])

    ReservationPlace.objects.create(
        reservation=reservation_2,
        seance=seance,
        salle=salle_1,
        place=place_1,
    )

    print("TEST 3 : place libérée puis réattribuée - OK")

    try:
        with transaction.atomic():
            ReservationPlace.objects.create(
                reservation=reservation_1,
                seance=seance,
                salle=salle_1,
                place=place_autre_salle,
            )
    except IntegrityError:
        print("TEST 4 : place d'une autre salle refusée - OK")
    else:
        raise AssertionError(
            "ERREUR : place d'une autre salle autorisée"
        )

    
    # TEST 5 : une attribution doit correspondre
    # à la séance de sa réservation.

    autre_seance = Seance.objects.create(
        film=film,
        salle=salle_2,
        date_debut=debut,
        date_fin=debut + timedelta(hours=2),
        prix=Decimal("10.00"),
    )

    try:
        with transaction.atomic():
            ReservationPlace.objects.create(
                reservation=reservation_1,
                seance=autre_seance,
                salle=salle_2,
                place=place_autre_salle,
            )
    except IntegrityError:
        print("TEST 5 : séance différente de la réservation refusée - OK")
    else:
        raise AssertionError(
            "ERREUR : séance incohérente autorisée"
        )

    # TEST 6 : la salle que je déclarée est
    # celle dans laquelle se déroule la séance.

    try:
        with transaction.atomic():
            ReservationPlace.objects.create(
                reservation=reservation_1,
                seance=seance,
                salle=salle_2,
                place=place_autre_salle,
            )
    except IntegrityError:
        print("TEST 6 : salle différente de celle de la séance refusée - OK")
    else:
        raise AssertionError(
            "ERREUR : salle incohérente autorisée"
        )

    transaction.set_rollback(True)

print("Tests terminés : données de test annulées.")
