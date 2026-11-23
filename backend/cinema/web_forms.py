from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Film, Utilisateur


class InscriptionForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ("email",)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = Utilisateur.Role.SPECTATEUR
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class FilmForm(forms.ModelForm):
    class Meta:
        model = Film
        fields = (
            "titre",
            "description",
            "duree_minutes",
            "genre",
            "date_sortie",
            "affiche_url",
            "est_publie",
        )

        labels = {
            "titre": "Titre du film",
            "description": "Description",
            "duree_minutes": "Durée (minutes)",
            "genre": "Genre",
            "date_sortie": "Date de sortie",
            "affiche_url": "URL de l'affiche",
            "est_publie": "Publier immédiatement",
        }

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "date_sortie": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_titre(self):
        titre = self.cleaned_data["titre"].strip()
        if not titre:
            raise forms.ValidationError("Le titre est obligatoire.")
        return titre

    def clean_duree_minutes(self):
        duree = self.cleaned_data["duree_minutes"]
        if duree <= 0:
            raise forms.ValidationError(
                "La durée doit être supérieure à zéro."
            )
        return duree
