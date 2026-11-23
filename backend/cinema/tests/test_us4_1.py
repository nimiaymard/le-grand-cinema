from django.test import TestCase
from django.urls import reverse

from cinema.models import Film, Utilisateur


class AjoutFilmTests(TestCase):
    def setUp(self):
        self.url = reverse("ajouter_film_web")

        self.admin = Utilisateur.objects.create_user(
            email="admin-us41@example.com",
            password="TestPass123!",
            role=Utilisateur.Role.ADMIN,
        )
        self.spectateur = Utilisateur.objects.create_user(
            email="spectateur-us41@example.com",
            password="TestPass123!",
        )

        self.donnees = {
            "titre": "Film de test",
            "description": "Description du film",
            "duree_minutes": 120,
            "est_publie": "on",
        }

    def test_anonyme_redirige(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_spectateur_refuse(self):
        self.client.force_login(self.spectateur)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_admin_accede_formulaire(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_admin_cree_film(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, self.donnees)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Film.objects.filter(
                titre="Film de test",
                est_publie=True,
            ).exists()
        )

    def test_titre_obligatoire(self):
        self.client.force_login(self.admin)
        donnees = {**self.donnees, "titre": ""}

        response = self.client.post(self.url, donnees)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Film.objects.exists())

    def test_duree_invalide(self):
        self.client.force_login(self.admin)
        donnees = {**self.donnees, "duree_minutes": -10}

        response = self.client.post(self.url, donnees)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Film.objects.exists())

    def test_brouillon_invisible_spectateur(self):
        film = Film.objects.create(
            titre="Film brouillon",
            duree_minutes=90,
            est_publie=False,
        )

        response = self.client.get(
            reverse("detail_film", args=[film.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_film_publie_visible(self):
        film = Film.objects.create(
            titre="Film publié",
            duree_minutes=90,
            est_publie=True,
        )

        response = self.client.get(
            reverse("detail_film", args=[film.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_consulte_brouillon(self):
        film = Film.objects.create(
            titre="Film brouillon",
            duree_minutes=90,
            est_publie=False,
        )

        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("detail_film", args=[film.pk])
        )
        self.assertEqual(response.status_code, 200)
