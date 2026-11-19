
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from cinema.models import Film, Salle, Seance


debut = timezone.make_aware(
    datetime(2026, 12, 1, 14, 0)
)

with transaction.atomic():
    film = Film.objects.create(
        titre="Film de test",
        duree_minutes=120,
    )

    salle_1 = Salle.objects.create(
        nom="Salle Test A",
        capacite=50,
    )

    salle_2 = Salle.objects.create(
        nom="Salle Test B",
        capacite=50,
    )

    Seance.objects.create(
        film=film,
        salle=salle_1,
        date_debut=debut,
        date_fin=debut + timedelta(hours=2),
        prix=Decimal("10.00"),
    )

    print("TEST 1 : première séance créée")

    try:
        with transaction.atomic():
            Seance.objects.create(
                film=film,
                salle=salle_1,
                date_debut=debut + timedelta(minutes=30),
                date_fin=debut + timedelta(hours=2, minutes=30),
                prix=Decimal("10.00"),
            )
    except IntegrityError:
        print("TEST 2 : chevauchement refusé - OK")
    else:
        raise AssertionError(
            "ERREUR : le chevauchement a été autorisé"
        )

    Seance.objects.create(
        film=film,
        salle=salle_2,
        date_debut=debut + timedelta(minutes=30),
        date_fin=debut + timedelta(hours=2, minutes=30),
        prix=Decimal("10.00"),
    )

    print("TEST 3 : autre salle autorisée - OK")

    Seance.objects.create(
        film=film,
        salle=salle_1,
        date_debut=debut + timedelta(hours=2),
        date_fin=debut + timedelta(hours=4),
        prix=Decimal("10.00"),
    )

    print("TEST 4 : séances consécutives autorisées - OK")

    transaction.set_rollback(True)

print("Tests terminés : données de test annulées.")
