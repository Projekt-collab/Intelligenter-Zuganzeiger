from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch
from django.shortcuts import render, redirect, get_object_or_404
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from web.models import Zug, Fahrt, Fahrstrasse, Gleis, StellwerkAnfrage


# Create your views here.
@login_required
def lokfuehrer_index(request):
    ist_lokfuehrer = request.user.groups.filter(name='Lokführer').exists()

    aktuelle_fahrt = Fahrt.objects.filter(
        lokfuehrer=request.user,
        fahrt_ende__isnull=True
    ).first()

    if not ist_lokfuehrer:
        messages.warning(request, "Sie sind kein Lockführer")
        return redirect('register')

    if not aktuelle_fahrt:
        return redirect('dashboard')

    return TemplateResponse(request, "lokfuehrer.html", {
        'aktuelle_fahrt': aktuelle_fahrt
    })

@login_required
def dispatcher_index(request):
    ist_dispatcher = request.user.groups.filter(name='Dispatcher').exists()

    if not ist_dispatcher:
        messages.warning(request, "Sie sind kein Dispatcher")
        return redirect('register')

    anfragen = StellwerkAnfrage.objects.filter(zugewiesenes_gleis__isnull=True, ergebnis='ABGEWIESEN').all().order_by('anfrage_zeit')[:2]
    aktive_fahrstrassen = Fahrstrasse.objects.filter(ist_aktiv=True).select_related('zug')
    gleise = Gleis.objects.prefetch_related(
        Prefetch('reservierungen', queryset=aktive_fahrstrassen, to_attr='aktive_reservierung')
    ).order_by('gleis_nummer')

    return TemplateResponse(request, "dispatcher.html", {
        'anfragen': anfragen,
        'gleise': gleise
    })

@login_required
@require_POST  # Sorgt dafür, dass die Fahrt nur per POST-Methode (Sicherheits-Button) beendet werden kann
def fahrt_beenden_view(request, fahrt_id):
    # Wir holen die Fahrt anhand der ID und stellen sicher, dass sie auch diesem User gehört
    fahrt = get_object_or_404(Fahrt, id=fahrt_id, lokfuehrer=request.user, fahrt_ende__isnull=True)
    fahrt.fahrt_ende = timezone.now()
    fahrt.save()

    zug = fahrt.zug
    zug.status = "WARTET"
    zug.save()

    fahrstrasse = Fahrstrasse.objects.filter(zug=zug, ist_aktiv=True).first()
    if fahrstrasse:
        fahrstrasse.freigeschaltet_um = timezone.now()
        fahrstrasse.ist_aktiv = False
        fahrstrasse.save()

        gleis = fahrstrasse.gleis
        gleis.sensor_belegt = False
        gleis.save()

    # Nach dem Beenden laden wir das Dashboard neu
    return redirect('dashboard')



