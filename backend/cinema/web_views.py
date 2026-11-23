from .models import Billet, Film, Place, Reservation, ReservationPlace, Seance
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Film, Place, Reservation, ReservationPlace, Seance

from .services import (
    ErreurReservation,
    annuler_reservation,
    creer_reservation,
)

from .notifications import (
    envoyer_confirmation_annulation,
    envoyer_confirmation_reservation,
)

from .web_forms import InscriptionForm


def catalogue_films(request):
    films = Film.objects.all()
    return render(request, "cinema/films.html", {"films": films})


def detail_film(request, film_id):
    film = get_object_or_404(Film, pk=film_id)

    seances = (
        Seance.objects.select_related("salle")
        .filter(
            film=film,
            statut=Seance.Statut.PROGRAMMEE,
            date_debut__gt=timezone.now(),
            salle__est_active=True,
        )
        .order_by("date_debut")
    )

    return render(
        request,
        "cinema/detail_film.html",
        {"film": film, "seances": seances},
    )


def liste_seances_web(request):
    seances = (
        Seance.objects.select_related("film", "salle")
        .filter(
            statut=Seance.Statut.PROGRAMMEE,
            date_debut__gt=timezone.now(),
            salle__est_active=True,
        )
        .order_by("date_debut")
    )

    return render(
        request,
        "cinema/seances.html",
        {"seances": seances},
    )


def inscription(request):
    if request.user.is_authenticated:
        return redirect("catalogue_films")

    form = InscriptionForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)

        messages.success(
            request,
            "Votre compte a été créé.",
        )
        return redirect("catalogue_films")

    return render(
        request,
        "registration/signup.html",
        {"form": form},
    )


@login_required
def reservation_web(request, seance_id):
    seance = get_object_or_404(
        Seance.objects.select_related("film", "salle"),
        pk=seance_id,
        statut=Seance.Statut.PROGRAMMEE,
        date_debut__gt=timezone.now(),
        salle__est_active=True,
    )

    if request.method == "POST":
        try:
            ids = [
                int(value)
                for value in request.POST.getlist("place_ids")
            ]

            reservation = creer_reservation(
                request.user,
                seance.id,
                ids,
            )

            # Envoyer l'email après validation de la transaction.
            transaction.on_commit(
                lambda reservation=reservation:
                    envoyer_confirmation_reservation(reservation)
            )

            messages.success(
                request,
                f"Réservation n°{reservation.id} confirmée.",
            )
            return redirect("mes_reservations_web")

        except ValueError:
            messages.error(
                request,
                "Sélection de places invalide.",
            )

        except ErreurReservation as exc:
            messages.error(request, str(exc))

    # Places actives de la salle.
    places = Place.objects.filter(
        salle=seance.salle,
        est_active=True,
    ).order_by("rangee", "numero")

    # Places déjà réservées.
    ids_occupes = set(
        ReservationPlace.objects.filter(
            seance=seance,
            date_liberation__isnull=True,
        ).values_list("place_id", flat=True)
    )

    plan_places = [
        {
            "id": place.id,
            "rangee": place.rangee,
            "numero": place.numero,
            "occupee": place.id in ids_occupes,
        }
        for place in places
    ]

    nb_disponibles = sum(
        not place["occupee"]
        for place in plan_places
    )

    return render(
        request,
        "cinema/reservation.html",
        {
            "seance": seance,
            "places": plan_places,
            "nb_disponibles": nb_disponibles,
        },
    )


@login_required
def mes_reservations_web(request):
    reservations = (
        Reservation.objects.filter(
            utilisateur=request.user
        )
        .select_related(
            "seance__film",
            "seance__salle",
        )
        .prefetch_related("places_reservees__place")
    )

    return render(
        request,
        "cinema/mes_reservations.html",
        {
            "reservations": reservations,
            "maintenant": timezone.now(),
        },
    )



@login_required
@require_POST
def annuler_reservation_web(request, reservation_id):
    try:
        reservation = annuler_reservation(
            reservation_id,
            request.user,
        )

        # Envoyer l'email uniquement après une annulation réussie
        # et après validation de la transaction.
        transaction.on_commit(
            lambda reservation=reservation:
                envoyer_confirmation_annulation(reservation)
        )

        messages.success(
            request,
            "Votre réservation a été annulée. "
            "Un email de confirmation vous a été envoyé.",
        )

    except ErreurReservation as exc:
        messages.error(request, str(exc))

    return redirect("mes_reservations_web")


@login_required
def billet_web(request, reservation_id):
    reservation = get_object_or_404(
        Reservation.objects.select_related(
            "utilisateur",
            "seance__film",
            "seance__salle",
        ),
        pk=reservation_id,
    )

    # Seul le propriétaire ou le personnel autorisé
    # peut consulter le billet.
    est_proprietaire = (
        reservation.utilisateur_id == request.user.id
    )

    est_personnel = (
        request.user.is_staff
        or request.user.is_superuser
    )

    if not (est_proprietaire or est_personnel):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    # Aucun billet valide pour une réservation annulée.
    if reservation.statut != Reservation.Statut.CONFIRMEE:
        from django.http import Http404
        raise Http404("Aucun billet valide pour cette réservation.")

    billet, _ = Billet.objects.get_or_create(
        reservation=reservation,
    )

    places = (
        ReservationPlace.objects.filter(
            reservation=reservation,
            date_liberation__isnull=True,
        )
        .select_related("place")
        .order_by("place__rangee", "place__numero")
    )

    return render(
        request,
        "cinema/billet.html",
        {
            "billet": billet,
            "reservation": reservation,
            "places": places,
        },
    )
