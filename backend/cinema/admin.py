
from django.contrib import admin

from .models import (
    Film,
    Place,
    Reservation,
    ReservationPlace,
    Salle,
    Seance,
)

admin.site.register(Film)
admin.site.register(Salle)
admin.site.register(Place)
admin.site.register(Seance)
admin.site.register(Reservation)
admin.site.register(ReservationPlace)
