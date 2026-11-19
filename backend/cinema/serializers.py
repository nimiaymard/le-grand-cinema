
from rest_framework import serializers


class FilmSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    titre = serializers.CharField()
    description = serializers.CharField()
    duree_minutes = serializers.IntegerField()
    genre = serializers.CharField()
    affiche_url = serializers.CharField(allow_blank=True, allow_null=True)


class SeanceSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    film = serializers.CharField()
    salle = serializers.CharField()
    date_debut = serializers.DateTimeField()
    date_fin = serializers.DateTimeField()
    prix = serializers.DecimalField(max_digits=10, decimal_places=2)


class PlaceDisponibleSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    rangee = serializers.CharField()
    numero = serializers.IntegerField()


class ReservationRequestSerializer(serializers.Serializer):
    seance_id = serializers.IntegerField(min_value=1)
    place_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )


class ReservationResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    statut = serializers.CharField()
    montant_total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    message = serializers.CharField()


class PlaceReserveeSerializer(serializers.Serializer):
    rangee = serializers.CharField()
    numero = serializers.IntegerField()


class MesReservationsSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    film = serializers.CharField()
    salle = serializers.CharField()
    date_debut = serializers.DateTimeField()
    statut = serializers.CharField()
    montant_total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    places = PlaceReserveeSerializer(many=True)


class AnnulationResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    statut = serializers.CharField()
    message = serializers.CharField()


class ErreurSerializer(serializers.Serializer):
    erreur = serializers.CharField()
