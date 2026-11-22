
from django.test import TestCase
from django.urls import reverse

from cinema.models import Film


class TestsCatalogueFilms(TestCase):

    def test_message_catalogue_vide(self):
        # Vérifier que la base de test ne contient aucun film
        self.assertEqual(Film.objects.count(), 0)

        # Accéder au catalogue sans authentification
        response = self.client.get(reverse("catalogue_films"))

        # Vérifier que la page est accessible
        self.assertEqual(response.status_code, 200)

        # Vérifier que le message attendu est affiché
        self.assertContains(
            response,
            "Aucun film disponible pour le moment."
        )
