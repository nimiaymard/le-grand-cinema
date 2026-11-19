
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Film, Reservation, Seance
from .services import (
    ErreurReservation,
    obtenir_places_disponibles,
    creer_reservation,
    annuler_reservation,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def liste_films(request):
    films = Film.objects.all()
    return Response([
        {
            "id": film.id,
            "titre": film.titre,
            "description": film.description,
            "duree_minutes": film.duree_minutes,
            "genre": film.genre,
            "affiche_url": film.affiche_url,
        }
        for film in films
    ])


@api_view(["GET"])
@permission_classes([AllowAny])
def liste_seances(request):
    seances = Seance.objects.select_related(
        "film", "salle"
    ).filter(
        statut=Seance.Statut.PROGRAMMEE
    ).order_by("date_debut")

    return Response([
        {
            "id": seance.id,
            "film": seance.film.titre,
            "salle": seance.salle.nom,
            "date_debut": seance.date_debut,
            "date_fin": seance.date_fin,
            "prix": str(seance.prix),
        }
        for seance in seances
    ])


@api_view(["GET"])
@permission_classes([AllowAny])
def places_disponibles(request, seance_id):
    get_object_or_404(Seance, pk=seance_id)

    places = obtenir_places_disponibles(seance_id)

    return Response([
        {
            "id": place.id,
            "rangee": place.rangee,
            "numero": place.numero,
        }
        for place in places
    ])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reserver(request):
    seance_id = request.data.get("seance_id")
    place_ids = request.data.get("place_ids")

    if type(seance_id) is not int or seance_id <= 0:
        return Response(
            {"erreur": "Identifiant de séance invalide."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        reservation = creer_reservation(
            request.user,
            seance_id,
            place_ids,
        )

        return Response(
            {
                "id": reservation.id,
                "statut": reservation.statut,
                "montant_total": str(reservation.montant_total),
                "message": "Réservation confirmée.",
            },
            status=status.HTTP_201_CREATED,
        )

    except ErreurReservation as exc:
        return Response(
            {"erreur": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mes_reservations(request):
    reservations = Reservation.objects.filter(
        utilisateur=request.user
    ).select_related("seance__film", "seance__salle").prefetch_related(
        "places_reservees__place"
    )

    return Response([
        {
            "id": reservation.id,
            "film": reservation.seance.film.titre,
            "salle": reservation.seance.salle.nom,
            "date_debut": reservation.seance.date_debut,
            "statut": reservation.statut,
            "montant_total": str(reservation.montant_total),
            "places": [
                {
                    "rangee": rp.place.rangee,
                    "numero": rp.place.numero,
                }
                for rp in reservation.places_reservees.all()
                if rp.date_liberation is None
            ],
        }
        for reservation in reservations
    ])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def annuler(request, reservation_id):
    try:
        reservation = annuler_reservation(
            reservation_id,
            request.user,
        )

        return Response({
            "id": reservation.id,
            "statut": reservation.statut,
            "message": "Réservation annulée.",
        })

    except ErreurReservation as exc:
        return Response(
            {"erreur": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

