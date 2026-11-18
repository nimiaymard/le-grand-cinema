from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    class Role(models.TextChoices):
        SPECTATEUR = "spectateur", "Spectateur"
        ADMIN = "admin", "Administrateur"

    username = None

    email = models.EmailField(unique=True)

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
