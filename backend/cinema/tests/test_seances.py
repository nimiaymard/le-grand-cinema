
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TransactionTestCase
from django.utils import timezone

from cinema.models import Film, Salle, Seance


class TestsSeances(TransactionTestCase):
    """Tests de création, de planification et de consultation des séances."""

    def setUp(self):
        self.debut = timezone.now() + timedelta(days=10)

        self.film = Film.objects.create(
            titre="Film de test",
            duree_minutes=120,
        )

        self.salle_1 = Salle.objects.create(
            nom="Salle Test A",
            capacite=50,
        )

        self.salle_2 = Salle.objects.create(
            nom="Salle Test B",
            capacite=50,
        )

    def creer_seance(self, salle, debut, fin):
        """Crée une séance programmée pour les tests."""
        return Seance.objects.create(
            film=self.film,
            salle=salle,
            date_debut=debut,
            date_fin=fin,
            prix=Decimal("10.00"),
        )

    # --------------------------------------------------
    # 1. Création des séances
    # --------------------------------------------------

    def test_creation_premiere_seance(self):
        seance = self.creer_seance(
            self.salle_1,
            self.debut,
            self.debut + timedelta(hours=2),
        )

        self.assertIsNotNone(seance.pk)

    # --------------------------------------------------
    # 2. Contraintes de planification
    # --------------------------------------------------

    def test_chevauchement_refuse(self):
        self.creer_seance(
            self.salle_1,
            self.debut,
            self.debut + timedelta(hours=2),
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.creer_seance(
                self.salle_1,
                self.debut + timedelta(minutes=30),
                self.debut + timedelta(hours=2, minutes=30),
            )

    def test_meme_horaire_autre_salle_autorise(self):
        self.creer_seance(
            self.salle_1,
            self.debut,
            self.debut + timedelta(hours=2),
        )

        autre = self.creer_seance(
            self.salle_2,
            self.debut + timedelta(minutes=30),
            self.debut + timedelta(hours=2, minutes=30),
        )

        self.assertIsNotNone(autre.pk)

    def test_seances_consecutives_autorisees(self):
        self.creer_seance(
            self.salle_1,
            self.debut,
            self.debut + timedelta(hours=2),
        )

        suivante = self.creer_seance(
            self.salle_1,
            self.debut + timedelta(hours=2),
            self.debut + timedelta(hours=4),
        )

        self.assertIsNotNone(suivante.pk)

    # --------------------------------------------------
    # 3. US 1.2 - Séances annulées
    # --------------------------------------------------

    def test_seance_annulee_absente_du_catalogue(self):
        """Une séance annulée ne doit pas être proposée au public."""

        # Création d'une séance annulée
        seance = Seance.objects.create(
            film=self.film,
            salle=self.salle_1,
            date_debut=self.debut,
            date_fin=self.debut + timedelta(hours=2),
            prix=Decimal("10.00"),
            statut=Seance.Statut.ANNULEE,
        )

        # Vérifier son statut en base
        self.assertEqual(
            seance.statut,
            Seance.Statut.ANNULEE,
        )

        # Vérifier son absence de la liste publique
        response = self.client.get("/seances/")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Film de test")

        # Simuler un spectateur authentifié
        utilisateur = get_user_model().objects.create_user(
            email="spectateur_test@example.com",
            password="MotDePasseTest123!",
        )
        self.client.force_login(utilisateur)

        # Tenter d'accéder directement à la réservation
        response_reservation = self.client.get(
            f"/seances/{seance.id}/reserver/"
        )

        # La séance annulée doit être inaccessible
        self.assertEqual(
            response_reservation.status_code,
            404,
        )


    def test_message_aucune_seance_pour_un_film(self):
        """Un film sans séance future affiche un message explicite."""

        # Le film créé dans setUp ne possède aucune séance
        self.assertFalse(
            Seance.objects.filter(film=self.film).exists()
        )

        # Consulter la fiche publique du film
        response = self.client.get(
            f"/films/{self.film.id}/"
        )

        # La page doit être accessible
        self.assertEqual(response.status_code, 200)

        # Le message d'absence de séances doit être affiché
        self.assertContains(
            response,
            "Aucune séance à venir pour ce film.",
        )
