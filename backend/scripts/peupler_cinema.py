
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from cinema.models import Film, Salle, Place, Seance


print("Création des données de démonstration...")

# 1. Films
films = [
    {
        "titre": "Le Voyage des Étoiles",
        "description": "Une aventure de science-fiction.",
        "duree_minutes": 125,
        "genre": "Science-fiction",
        "date_sortie": date(2026, 10, 15),
        "affiche_url": "",
    },
    {
        "titre": "Les Secrets de Bordeaux",
        "description": "Un thriller au cœur de Bordeaux.",
        "duree_minutes": 110,
        "genre": "Thriller",
        "date_sortie": date(2026, 11, 5),
        "affiche_url": "",
    },
    {
        "titre": "Jazz sous les Étoiles",
        "description": "Un film musical autour du jazz.",
        "duree_minutes": 95,
        "genre": "Musical",
        "date_sortie": date(2026, 11, 12),
        "affiche_url": "",
    },
]

films_crees = []

for donnees in films:
    film, _ = Film.objects.get_or_create(
        titre=donnees["titre"],
        defaults=donnees,
    )
    films_crees.append(film)

# 2. Salles et places
salles = []

for numero in range(1, 4):
    salle, _ = Salle.objects.get_or_create(
        nom=f"Salle {numero}",
        defaults={
            "capacite": 20,
            "est_active": True,
        },
    )
    salles.append(salle)

    for rangee in ["A", "B", "C", "D"]:
        for numero_place in range(1, 6):
            Place.objects.get_or_create(
                salle=salle,
                rangee=rangee,
                numero=numero_place,
                defaults={"est_active": True},
            )

# 3. Séances futures
# Créneaux suffisamment espacés pour éviter les chevauchements.
base = timezone.now() + timedelta(days=2)
base = base.replace(hour=14, minute=0, second=0, microsecond=0)

for index, film in enumerate(films_crees):
    debut = base + timedelta(hours=index * 4)
    fin = debut + timedelta(minutes=film.duree_minutes)

    Seance.objects.get_or_create(
        film=film,
        salle=salles[index],
        date_debut=debut,
        defaults={
            "date_fin": fin,
            "prix": Decimal("9.50"),
            "statut": "programmee",
        },
    )

print("Données créées avec succès.")
print("Films :", Film.objects.count())
print("Salles :", Salle.objects.count())
print("Places :", Place.objects.count())
print("Séances :", Seance.objects.count())
