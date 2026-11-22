
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.utils import timezone

from rest_framework.test import APIClient

from cinema.models import (
    Film,
    Salle,
    Place,
    Seance,
    Reservation,
    ReservationPlace,
)


class TestsAPI(TransactionTestCase):

    def setUp(self):
        self.client = APIClient()

        User = get_user_model()

        self.utilisateur = User.objects.create_user(
            email="api.test@example.com",
            password="MotDePasseTest123!",
        )

        self.autre_utilisateur = User.objects.create_user(
            email="autre.api@example.com",
            password="MotDePasseTest123!",
        )

        self.film = Film.objects.create(
            titre="Film API",
            description="Film de démonstration",
            duree_minutes=120,
            genre="Drame",
        )

        self.salle = Salle.objects.create(
            nom="Salle API",
            capacite=2,
            est_active=True,
        )

        self.place_1 = Place.objects.create(
            salle=self.salle,
            rangee="A",
            numero=1,
            est_active=True,
        )

        self.place_2 = Place.objects.create(
            salle=self.salle,
            rangee="A",
            numero=2,
            est_active=True,
        )

        debut = timezone.now() + timedelta(days=10)

        self.seance = Seance.objects.create(
            film=self.film,
            salle=self.salle,
            date_debut=debut,
            date_fin=debut + timedelta(hours=2),
            prix=Decimal("9.50"),
            statut=Seance.Statut.PROGRAMMEE,
        )

    def authentifier(self):
        self.client.force_authenticate(user=self.utilisateur)

    def reserver(self, places=None):
        return self.client.post(
            "/api/reservations/",
            {
                "seance_id": self.seance.id,
                "place_ids": places or [
                    self.place_1.id,
                    self.place_2.id,
                ],
            },
            format="json",
        )

    def test_liste_films_publique(self):
        reponse = self.client.get("/api/films/")

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(len(reponse.data), 1)
        self.assertEqual(reponse.data[0]["titre"], "Film API")

    def test_liste_seances_publique(self):
        reponse = self.client.get("/api/seances/")

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(len(reponse.data), 1)

    def test_places_disponibles(self):
        reponse = self.client.get(
            f"/api/seances/{self.seance.id}/places/"
        )

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(len(reponse.data), 2)

    def test_reservation_authentification_obligatoire(self):
        reponse = self.reserver()

        self.assertIn(reponse.status_code, [401, 403])
        self.assertEqual(Reservation.objects.count(), 0)

    def test_creation_reservation(self):
        self.authentifier()

        reponse = self.reserver()

        self.assertEqual(reponse.status_code, 201)
        self.assertEqual(reponse.data["statut"], "confirmee")
        self.assertEqual(reponse.data["montant_total"], "19.00")
        self.assertEqual(Reservation.objects.count(), 1)

    def test_places_indisponibles_apres_reservation(self):
        self.authentifier()
        self.reserver()

        reponse = self.client.get(
            f"/api/seances/{self.seance.id}/places/"
        )

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(len(reponse.data), 0)

    def test_double_reservation_refusee(self):
        self.authentifier()

        premiere = self.reserver()
        seconde = self.reserver()

        self.assertEqual(premiere.status_code, 201)
        self.assertEqual(seconde.status_code, 400)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_consultation_mes_reservations(self):
        self.authentifier()
        self.reserver()

        reponse = self.client.get("/api/mes-reservations/")

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(len(reponse.data), 1)
        self.assertEqual(len(reponse.data[0]["places"]), 2)

    def test_annulation_reservation(self):
        self.authentifier()

        creation = self.reserver()
        reservation_id = creation.data["id"]

        reponse = self.client.post(
            f"/api/reservations/{reservation_id}/annuler/",
            format="json",
        )

        self.assertEqual(reponse.status_code, 200)

        reservation = Reservation.objects.get(pk=reservation_id)
        self.assertEqual(
            reservation.statut,
            Reservation.Statut.ANNULEE,
        )

        self.assertEqual(
            ReservationPlace.objects.filter(
                reservation=reservation,
                date_liberation__isnull=True,
            ).count(),
            0,
        )

        disponibilites = self.client.get(
            f"/api/seances/{self.seance.id}/places/"
        )
        self.assertEqual(len(disponibilites.data), 2)

    def test_annulation_reservation_autre_utilisateur_refusee(self):
        self.authentifier()

        creation = self.reserver()
        reservation_id = creation.data["id"]

        self.client.force_authenticate(
            user=self.autre_utilisateur
        )

        reponse = self.client.post(
            f"/api/reservations/{reservation_id}/annuler/",
            format="json",
        )

        self.assertEqual(reponse.status_code, 400)

        reservation = Reservation.objects.get(pk=reservation_id)
        self.assertEqual(
            reservation.statut,
            Reservation.Statut.CONFIRMEE,
        )
