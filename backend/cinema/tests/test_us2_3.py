
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from cinema.models import (
    Film,
    Place,
    Reservation,
    ReservationPlace,
    Salle,
    Seance,
)
from cinema.services import (
    ErreurReservation,
    annuler_reservation,
    creer_reservation,
)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
class AnnulationUS23Tests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.user = User.objects.create_user(
            email="client-us23@example.com",
            password="TestPass123!",
        )

        cls.autre = User.objects.create_user(
            email="autre-us23@example.com",
            password="TestPass123!",
        )

        # Film
        cls.film = Film.objects.create(
            titre="Film test US 2.3",
            duree_minutes=120,
        )

        # Salle
        cls.salle = Salle.objects.create(
            nom="Salle US23",
            capacite=20,
            est_active=True,
        )

        # Place
        cls.place = Place.objects.create(
            salle=cls.salle,
            rangee="A",
            numero=1,
            est_active=True,
        )

        # Séance
        debut = timezone.now() + timedelta(days=2)

        cls.seance = Seance.objects.create(
            film=cls.film,
            salle=cls.salle,
            date_debut=debut,
            date_fin=debut + timedelta(minutes=120),
            prix=Decimal("9.50"),
            statut=Seance.Statut.PROGRAMMEE,
        )

    def setUp(self):
        self.reservation = creer_reservation(
            self.user,
            self.seance.id,
            [self.place.id],
        )

    def test_annulation_met_a_jour_statut_et_libere_place(self):
        annuler_reservation(
            self.reservation.id,
            self.user,
        )

        self.reservation.refresh_from_db()

        self.assertEqual(
            self.reservation.statut,
            Reservation.Statut.ANNULEE,
        )

        self.assertFalse(
            ReservationPlace.objects.filter(
                reservation=self.reservation,
                date_liberation__isnull=True,
            ).exists()
        )

    def test_double_annulation_refusee(self):
        annuler_reservation(
            self.reservation.id,
            self.user,
        )

        with self.assertRaises(ErreurReservation):
            annuler_reservation(
                self.reservation.id,
                self.user,
            )

    def test_autre_utilisateur_ne_peut_pas_annuler(self):
        with self.assertRaises(ErreurReservation):
            annuler_reservation(
                self.reservation.id,
                self.autre,
            )

    def test_place_redevient_reservable(self):
        annuler_reservation(
            self.reservation.id,
            self.user,
        )

        nouvelle = creer_reservation(
            self.autre,
            self.seance.id,
            [self.place.id],
        )

        self.assertEqual(
            nouvelle.statut,
            Reservation.Statut.CONFIRMEE,
        )

    def test_email_apres_annulation_reussie(self):
        self.client.force_login(self.user)

        with patch(
            "cinema.web_views.envoyer_confirmation_annulation"
        ) as envoyer:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    reverse(
                        "annuler_reservation_web",
                        args=[self.reservation.id],
                    )
                )

        self.assertEqual(
            response.status_code,
            302,
        )

        envoyer.assert_called_once()

    def test_aucun_email_si_annulation_refusee(self):
        self.client.force_login(self.autre)

        with patch(
            "cinema.web_views.envoyer_confirmation_annulation"
        ) as envoyer:
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post(
                    reverse(
                        "annuler_reservation_web",
                        args=[self.reservation.id],
                    )
                )

        envoyer.assert_not_called()

    def test_authentification_obligatoire(self):
        response = self.client.post(
            reverse(
                "annuler_reservation_web",
                args=[self.reservation.id],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            "/connexion/",
            response.url,
        )
