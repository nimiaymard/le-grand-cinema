
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier

from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase
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
from cinema.services import ErreurReservation, creer_reservation


class TestsUS22Reservation(TestCase):

    def setUp(self):
        self.utilisateur = Utilisateur.objects.create_user(
            email="us22@example.com",
            password="MotDePasseTest123!",
        )

        self.film = Film.objects.create(
            titre="Film US 2.2",
            duree_minutes=120,
        )

        self.salle = Salle.objects.create(
            nom="Salle US 2.2",
            capacite=3,
            est_active=True,
        )

        self.places = [
            Place.objects.create(
                salle=self.salle,
                rangee="A",
                numero=numero,
                est_active=True,
            )
            for numero in range(1, 4)
        ]

        debut = timezone.now() + timedelta(days=10)

        self.seance = Seance.objects.create(
            film=self.film,
            salle=self.salle,
            date_debut=debut,
            date_fin=debut + timedelta(hours=2),
            prix=Decimal("9.50"),
            statut=Seance.Statut.PROGRAMMEE,
        )

    def verifier_aucune_reservation(self):
        self.assertEqual(Reservation.objects.count(), 0)
        self.assertEqual(ReservationPlace.objects.count(), 0)

    def test_authentification_obligatoire(self):
        with self.assertRaisesMessage(
            ErreurReservation, "Authentification obligatoire"
        ):
            creer_reservation(
                AnonymousUser(),
                self.seance.id,
                [self.places[0].id],
            )

        self.verifier_aucune_reservation()

    def test_reserver_une_place(self):
        reservation = creer_reservation(
            self.utilisateur,
            self.seance.id,
            [self.places[0].id],
        )

        self.assertEqual(
            reservation.statut, Reservation.Statut.CONFIRMEE
        )
        self.assertEqual(
            reservation.montant_total, Decimal("9.50")
        )
        self.assertEqual(ReservationPlace.objects.count(), 1)

    def test_reserver_plusieurs_places(self):
        reservation = creer_reservation(
            self.utilisateur,
            self.seance.id,
            [place.id for place in self.places],
        )

        self.assertEqual(
            reservation.montant_total, Decimal("28.50")
        )
        self.assertEqual(ReservationPlace.objects.count(), 3)

    def test_reservation_associee_utilisateur(self):
        reservation = creer_reservation(
            self.utilisateur,
            self.seance.id,
            [self.places[0].id],
        )

        self.assertEqual(
            reservation.utilisateur_id, self.utilisateur.id
        )
        self.assertEqual(
            reservation.seance_id, self.seance.id
        )

    def test_liste_vide_refusee(self):
        with self.assertRaisesMessage(
            ErreurReservation, "Sélectionnez au moins une place"
        ):
            creer_reservation(
                self.utilisateur, self.seance.id, []
            )

        self.verifier_aucune_reservation()

    def test_identifiants_invalides_refuses(self):
        with self.assertRaisesMessage(
            ErreurReservation, "Identifiants de places invalides"
        ):
            creer_reservation(
                self.utilisateur, self.seance.id, [-1]
            )

        self.verifier_aucune_reservation()

    def test_place_selectionnee_deux_fois_refusee(self):
        place_id = self.places[0].id

        with self.assertRaisesMessage(
            ErreurReservation,
            "Une place a été sélectionnée plusieurs fois",
        ):
            creer_reservation(
                self.utilisateur,
                self.seance.id,
                [place_id, place_id],
            )

        self.verifier_aucune_reservation()

    def test_place_occupee_aucune_reservation_partielle(self):
        creer_reservation(
            self.utilisateur,
            self.seance.id,
            [self.places[0].id],
        )

        with self.assertRaisesMessage(
            ErreurReservation,
            "Une ou plusieurs places sont déjà réservées",
        ):
            creer_reservation(
                self.utilisateur,
                self.seance.id,
                [self.places[0].id, self.places[1].id],
            )

        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(ReservationPlace.objects.count(), 1)

        self.assertFalse(
            ReservationPlace.objects.filter(
                seance=self.seance,
                place=self.places[1],
                date_liberation__isnull=True,
            ).exists()
        )

class TestsConcurrenceUS22(TransactionTestCase):
    """Vérifie deux demandes simultanées sur une même place."""

    def setUp(self):
        self.utilisateurs = [
            Utilisateur.objects.create_user(
                email=f"concurrence{i}@example.com",
                password="MotDePasseTest123!",
            )
            for i in range(2)
        ]

        film = Film.objects.create(
            titre="Film concurrence US 2.2",
            duree_minutes=120,
        )

        salle = Salle.objects.create(
            nom="Salle concurrence US 2.2",
            capacite=1,
            est_active=True,
        )

        self.place = Place.objects.create(
            salle=salle,
            rangee="A",
            numero=1,
            est_active=True,
        )

        debut = timezone.now() + timedelta(days=10)

        self.seance = Seance.objects.create(
            film=film,
            salle=salle,
            date_debut=debut,
            date_fin=debut + timedelta(hours=2),
            prix=Decimal("9.50"),
            statut=Seance.Statut.PROGRAMMEE,
        )

    def test_deux_utilisateurs_meme_place(self):
        barriere = Barrier(2)

        def reserver(utilisateur):
            close_old_connections()

            try:
                barriere.wait(timeout=10)

                creer_reservation(
                    utilisateur,
                    self.seance.id,
                    [self.place.id],
                )

                return "succes"

            except ErreurReservation:
                return "refus"

            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultats = list(
                executor.map(reserver, self.utilisateurs)
            )

        self.assertCountEqual(
            resultats,
            ["succes", "refus"],
        )

        self.assertEqual(
            Reservation.objects.count(),
            1,
        )

        self.assertEqual(
            ReservationPlace.objects.filter(
                seance=self.seance,
                place=self.place,
                date_liberation__isnull=True,
            ).count(),
            1,
        )
