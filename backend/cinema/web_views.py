from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Film, Reservation, Seance
from .services import ErreurReservation, annuler_reservation, creer_reservation, obtenir_places_disponibles
from .web_forms import InscriptionForm


def catalogue_films(request):
    return render(request, "cinema/films.html", {"films": Film.objects.all()})


def detail_film(request, film_id):
    film = get_object_or_404(Film, pk=film_id)
    seances = Seance.objects.select_related("salle").filter(
        film=film, statut=Seance.Statut.PROGRAMMEE,
        date_debut__gt=timezone.now(), salle__est_active=True,
    ).order_by("date_debut")
    return render(request, "cinema/detail_film.html", {"film": film, "seances": seances})


def liste_seances_web(request):
    seances = Seance.objects.select_related("film", "salle").filter(
        statut=Seance.Statut.PROGRAMMEE,
        date_debut__gt=timezone.now(), salle__est_active=True,
    ).order_by("date_debut")
    return render(request, "cinema/seances.html", {"seances": seances})


def inscription(request):
    if request.user.is_authenticated:
        return redirect("catalogue_films")
    form = InscriptionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Votre compte a été créé.")
        return redirect("catalogue_films")
    return render(request, "registration/signup.html", {"form": form})


@login_required
def reservation_web(request, seance_id):
    seance = get_object_or_404(
        Seance.objects.select_related("film", "salle"),
        pk=seance_id, statut=Seance.Statut.PROGRAMMEE,
        date_debut__gt=timezone.now(), salle__est_active=True,
    )
    if request.method == "POST":
        try:
            ids = [int(x) for x in request.POST.getlist("place_ids")]
            reservation = creer_reservation(request.user, seance.id, ids)
            messages.success(request, f"Réservation n°{reservation.id} confirmée.")
            return redirect("mes_reservations_web")
        except ValueError:
            messages.error(request, "Sélection de places invalide.")
        except ErreurReservation as exc:
            messages.error(request, str(exc))
    places = obtenir_places_disponibles(seance.id)
    return render(request, "cinema/reservation.html", {"seance": seance, "places": places})


@login_required
def mes_reservations_web(request):
    reservations = Reservation.objects.filter(utilisateur=request.user).select_related(
        "seance__film", "seance__salle"
    ).prefetch_related("places_reservees__place")
    return render(request, "cinema/mes_reservations.html", {
        "reservations": reservations, "maintenant": timezone.now()
    })


@login_required
@require_POST
def annuler_reservation_web(request, reservation_id):
    try:
        annuler_reservation(reservation_id, request.user)
        messages.success(request, "Votre réservation a été annulée.")
    except ErreurReservation as exc:
        messages.error(request, str(exc))
    return redirect("mes_reservations_web")
