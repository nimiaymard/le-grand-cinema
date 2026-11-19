
from django.urls import path

from . import views

urlpatterns = [
    path("films/", views.liste_films, name="liste_films"),
    path("seances/", views.liste_seances, name="liste_seances"),
    path(
        "seances/<int:seance_id>/places/",
        views.places_disponibles,
        name="places_disponibles",
    ),
    path("reservations/", views.reserver, name="reserver"),
    path(
        "mes-reservations/",
        views.mes_reservations,
        name="mes_reservations",
    ),
    path(
        "reservations/<int:reservation_id>/annuler/",
        views.annuler,
        name="annuler_reservation",
    ),
]
