
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TransactionTestCase
from django.utils import timezone

from cinema.models import Film, Salle, Seance


class TestsSeances(TransactionTestCase):

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
        return Seance.objects.create(
            film=self.film,
            salle=salle,
            date_debut=debut,
            date_fin=fin,
            prix=Decimal("10.00"),
        )

    def test_creation_premiere_seance(self):
        seance = self.creer_seance(
            self.salle_1,
            self.debut,
            self.debut + timedelta(hours=2),
        )

        self.assertIsNotNone(seance.pk)

    def test_chevauchement_refuse(self):
        self.creer_seance(
            self.salle_1,
            self.debut,
            self.debut + timedelta(hours=2),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
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
