from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from cinema import web_views

urlpatterns = [
    path("seances/", web_views.liste_seances_web, name="liste_seances_web"),
    path("inscription/", web_views.inscription, name="inscription"),
    path(
        "connexion/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "seances/<int:seance_id>/reserver/",
        web_views.reservation_web,
        name="reservation_web",
    ),
    path(
        "mes-reservations/", web_views.mes_reservations_web, name="mes_reservations_web"
    ),
    path(
        "mes-reservations/<int:reservation_id>/annuler/",
        web_views.annuler_reservation_web,
        name="annuler_reservation_web",
    ),
    path("films/<int:film_id>/", web_views.detail_film, name="detail_film"),
    path("films/", web_views.catalogue_films, name="catalogue_films"),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("admin/", admin.site.urls),
    path(
        "reservations/<int:reservation_id>/billet/",
        web_views.billet_web,
        name="billet_web",
    ),
    # API REST du cinéma
    path("api/", include("cinema.urls")),
    # Authentification Django REST Framework
    path("api-auth/", include("rest_framework.urls")),
    # Documentation OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
