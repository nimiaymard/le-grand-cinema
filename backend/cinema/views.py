
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Film, Reservation, Seance
from .serializers import (
    AnnulationResponseSerializer,
    ErreurSerializer,
    FilmSerializer,
    MesReservationsSerializer,
    PlaceDisponibleSerializer,
    ReservationRequestSerializer,
    ReservationResponseSerializer,
    SeanceSerializer,
)
from .services import (
    ErreurReservation,
    annuler_reservation,
    creer_reservation,
    obtenir_places_disponibles,
)


@extend_schema(
    methods=["GET"],
    summary="Lister les films",
    description="Retourne la liste des films du cinéma.",
    responses={200: FilmSerializer(many=True)},
    tags=["Films"],
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



@extend_schema(
    methods=["GET"],
    summary="Lister les séances",
    description="Retourne les séances programmées du cinéma.",
    responses={200: SeanceSerializer(many=True)},
    tags=["Séances"],
)
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



@extend_schema(
    methods=["GET"],
    summary="Consulter les places disponibles",
    description="Retourne les places disponibles pour une séance.",
    responses={
        200: PlaceDisponibleSerializer(many=True),
        404: None,
    },
    tags=["Séances"],
)
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



@extend_schema(
    methods=["POST"],
    summary="Réserver des places",
    description="Crée une réservation pour un utilisateur authentifié.",
    request=ReservationRequestSerializer,
    responses={
        201: ReservationResponseSerializer,
        400: ErreurSerializer,
        401: None,
        403: None,
    },
    tags=["Réservations"],
)
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



@extend_schema(
    methods=["GET"],
    summary="Consulter mes réservations",
    description="Retourne les réservations de l'utilisateur connecté.",
    responses={
        200: MesReservationsSerializer(many=True),
        401: None,
        403: None,
    },
    tags=["Réservations"],
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



@extend_schema(
    methods=["POST"],
    summary="Annuler une réservation",
    description="Annule une réservation et libère les places associées.",
    request=None,
    responses={
        200: AnnulationResponseSerializer,
        400: ErreurSerializer,
        401: None,
        403: None,
    },
    tags=["Réservations"],
)
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

