from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur


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
