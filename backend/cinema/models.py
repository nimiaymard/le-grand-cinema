import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.db import models
from django.db.models import Func

from .managers import UtilisateurManager


class TstzRange(Func):
    function = "TSTZRANGE"
    output_field = DateTimeRangeField()


class Utilisateur(AbstractUser):
    class Role(models.TextChoices):
        SPECTATEUR = "spectateur", "Spectateur"
        ADMIN = "admin", "Administrateur"

    username = None

    email = models.EmailField(unique=True)
    
    objects = UtilisateurManager()   

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.SPECTATEUR,
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Film(models.Model):
    titre = models.CharField(max_length=200)

    description = models.TextField(
        null=True,
        blank=True,
    )

    duree_minutes = models.IntegerField()

    genre = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    date_sortie = models.DateField(
        null=True,
        blank=True,
    )

    affiche_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duree_minutes__gt=0),
                name="chk_film_duree",
            ),
        ]
        ordering = ["titre"]

    def __str__(self):
        return self.titre


class Salle(models.Model):
    nom = models.CharField(
        max_length=100,
        unique=True,
    )

    capacite = models.IntegerField()

    est_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacite__gt=0),
                name="chk_salle_capacite",
            ),
        ]
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Place(models.Model):
    salle = models.ForeignKey(
        Salle,
        on_delete=models.PROTECT,
        related_name="places",
    )

    rangee = models.CharField(max_length=5)

    numero = models.IntegerField()

    est_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["salle", "rangee", "numero"],
                name="uq_place_salle",
            ),
            models.CheckConstraint(
                condition=models.Q(numero__gt=0),
                name="chk_place_numero",
            ),
            models.UniqueConstraint(
                fields=["id", "salle"],
                name="uq_place_id_salle",
            ),
        ]
        ordering = ["salle", "rangee", "numero"]

    def __str__(self):
        return f"{self.salle.nom} - {self.rangee}{self.numero}"


class Seance(models.Model):
    class Statut(models.TextChoices):
        PROGRAMMEE = "programmee", "Programmée"
        ANNULEE = "annulee", "Annulée"
        TERMINEE = "terminee", "Terminée"

    film = models.ForeignKey(
        Film,
        on_delete=models.PROTECT,
        related_name="seances",
    )

    salle = models.ForeignKey(
        Salle,
        on_delete=models.PROTECT,
        related_name="seances",
    )

    date_debut = models.DateTimeField()

    date_fin = models.DateTimeField()

    prix = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.PROGRAMMEE,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    date_fin__gt=models.F("date_debut")
                ),
                name="chk_seance_dates",
            ),
            models.CheckConstraint(
                condition=models.Q(prix__gte=0),
                name="chk_seance_prix",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    statut__in=[
                        "programmee",
                        "annulee",
                        "terminee",
                    ]
                ),
                name="chk_seance_statut",
            ),
            models.UniqueConstraint(
                fields=["id", "salle"],
                name="uq_seance_id_salle",
            ),
            ExclusionConstraint(
                name="excl_chevauchement_seances",
                expressions=[
                    ("salle", RangeOperators.EQUAL),
                    (
                        TstzRange(
                            "date_debut",
                            "date_fin",
                            models.Value("[)"),
                        ),
                        RangeOperators.OVERLAPS,
                    ),
                ],
                condition=models.Q(statut="programmee"),
            ),
        ]
        ordering = ["date_debut"]

    def __str__(self):
        return f"{self.film.titre} - {self.date_debut}"


class Reservation(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        CONFIRMEE = "confirmee", "Confirmée"
        ANNULEE = "annulee", "Annulée"

    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name="reservations",
    )

    seance = models.ForeignKey(
        Seance,
        on_delete=models.PROTECT,
        related_name="reservations",
    )

    date_reservation = models.DateTimeField(
        auto_now_add=True,
    )

    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
    )

    montant_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    statut__in=[
                        "en_attente",
                        "confirmee",
                        "annulee",
                    ]
                ),
                name="chk_reservation_statut",
            ),
            models.CheckConstraint(
                condition=models.Q(montant_total__gte=0),
                name="chk_reservation_montant",
            ),
            models.UniqueConstraint(
                fields=["id", "seance"],
                name="uq_reservation_id_seance",
            ),
        ]
        ordering = ["-date_reservation"]

    def __str__(self):
        return f"Réservation {self.pk} - {self.statut}"

class ReservationPlace(models.Model):
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.PROTECT,
        related_name="places_reservees",
    )

    seance = models.ForeignKey(
        Seance,
        on_delete=models.PROTECT,
        related_name="places_reservees",
    )

    salle = models.ForeignKey(
        Salle,
        on_delete=models.PROTECT,
        related_name="places_reservees",
    )

    place = models.ForeignKey(
        Place,
        on_delete=models.PROTECT,
        related_name="reservations_places",
    )

    date_liberation = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["seance", "place"],
                condition=models.Q(date_liberation__isnull=True),
                name="uq_place_active_par_seance",
            ),
        ]

    def __str__(self):
        return f"Réservation {self.reservation_id} - Place {self.place_id}"

class Billet(models.Model):
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.PROTECT,
        related_name="billet",
    )

    reference = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    date_creation = models.DateTimeField(
        auto_now_add=True,
    )

    @property
    def est_valide(self):
        return self.reservation.statut == Reservation.Statut.CONFIRMEE

    def __str__(self):
        return f"Billet {self.reference}"
