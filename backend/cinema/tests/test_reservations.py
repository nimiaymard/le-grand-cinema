
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TransactionTestCase
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


class TestsContraintesReservation(TransactionTestCase):

    def setUp(self):
        debut = timezone.now() + timedelta(days=10)

        self.film = Film.objects.create(
            titre="Film test réservations",
            duree_minutes=120,
        )

        self.salle_1 = Salle.objects.create(
            nom="Salle Test Réservation A",
            capacite=20,
        )

        self.salle_2 = Salle.objects.create(
            nom="Salle Test Réservation B",
            capacite=20,
        )

        self.place_1 = Place.objects.create(
            salle=self.salle_1,
            rangee="A",
            numero=1,
        )

        self.place_autre_salle = Place.objects.create(
            salle=self.salle_2,
            rangee="A",
            numero=1,
        )

        self.seance = Seance.objects.create(
            film=self.film,
            salle=self.salle_1,
            date_debut=debut,
            date_fin=debut + timedelta(hours=2),
            prix=Decimal("10.00"),
        )

        self.utilisateur_1 = Utilisateur.objects.create_user(
            email="test.reservation1@example.com",
            password="TestTemporaire123!",
        )

        self.utilisateur_2 = Utilisateur.objects.create_user(
            email="test.reservation2@example.com",
            password="TestTemporaire123!",
        )

        self.reservation_1 = Reservation.objects.create(
            utilisateur=self.utilisateur_1,
            seance=self.seance,
            montant_total=Decimal("10.00"),
        )

        self.reservation_2 = Reservation.objects.create(
            utilisateur=self.utilisateur_2,
            seance=self.seance,
            montant_total=Decimal("10.00"),
        )

    def attribuer(self, reservation, seance, salle, place):
        return ReservationPlace.objects.create(
            reservation=reservation,
            seance=seance,
            salle=salle,
            place=place,
        )

    def test_premiere_reservation_autorisee(self):
        attribution = self.attribuer(
            self.reservation_1,
            self.seance,
            self.salle_1,
            self.place_1,
        )

        self.assertIsNotNone(attribution.pk)

    def test_double_reservation_refusee(self):
        self.attribuer(
            self.reservation_1,
            self.seance,
            self.salle_1,
            self.place_1,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.attribuer(
                self.reservation_2,
                self.seance,
                self.salle_1,
                self.place_1,
            )

    def test_place_liberee_puis_reattribuee(self):
        attribution = self.attribuer(
            self.reservation_1,
            self.seance,
            self.salle_1,
            self.place_1,
        )

        attribution.date_liberation = timezone.now()
        attribution.save(update_fields=["date_liberation"])

        nouvelle = self.attribuer(
            self.reservation_2,
            self.seance,
            self.salle_1,
            self.place_1,
        )

        self.assertIsNotNone(nouvelle.pk)

    def test_place_autre_salle_refusee(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.attribuer(
                self.reservation_1,
                self.seance,
                self.salle_1,
                self.place_autre_salle,
            )

    def test_seance_incoherente_refusee(self):
        debut = self.seance.date_debut

        autre_seance = Seance.objects.create(
            film=self.film,
            salle=self.salle_2,
            date_debut=debut,
            date_fin=debut + timedelta(hours=2),
            prix=Decimal("10.00"),
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.attribuer(
                self.reservation_1,
                autre_seance,
                self.salle_2,
                self.place_autre_salle,
            )

    def test_salle_incoherente_refusee(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.attribuer(
                self.reservation_1,
                self.seance,
                self.salle_2,
                self.place_autre_salle,
            )
