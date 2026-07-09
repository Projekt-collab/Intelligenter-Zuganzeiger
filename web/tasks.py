from celery import shared_task
from django.utils import timezone
from django.db import transaction
from web.models import Fahrstrasse, Fahrt, StellwerkAnfrage
from web.utils import send_stellwerk_update, send_zug_redirect


@shared_task
def gleis_automatisch_freigeben(fahrstrasse_id):

    jetzt = timezone.now()
    print(f"[CELERY] 2 Minuten sind vergangen. Start des Abfahrtsverfahrens für Fahrstraße ID: {fahrstrasse_id}...")

    try:
        with transaction.atomic():
            fahrstrasse = Fahrstrasse.objects.select_related('zug', 'gleis').get(id=fahrstrasse_id)

            if not fahrstrasse.ist_aktiv:
                print(f"[CELERY] Fahrstraße {fahrstrasse_id} wurde bereits zuvor deaktiviert. Abruch.")
                return "Schon fertig!"

            zug = fahrstrasse.zug
            gleis = fahrstrasse.gleis

            if zug.status in ['GEPARKT', 'FAHRT']:
                zug.status = 'ABGEFAHREN'
                zug.save()

            anfrage = StellwerkAnfrage.objects.filter(
                zug=zug,
                ergebnis='GENEHMIGT',
                zugewiesenes_gleis__isnull=False
            ).first()

            if anfrage:
                anfrage.ergebnis = 'BEENDEN'
                anfrage.save()

            aktive_fahrt = Fahrt.objects.filter(zug=zug, fahrt_ende__isnull=True).first()
            if aktive_fahrt:
                aktive_fahrt.fahrt_ende = jetzt
                aktive_fahrt.save()

            fahrstrasse.ist_aktiv = False
            fahrstrasse.save()

            gleis.sensor_belegt = False
            gleis.save()

            send_stellwerk_update(f"🛑 {zug.zug_nummer} hat erfolgreich beendet")

            send_zug_redirect(zug.zug_nummer)

            print(f"[🟢 ERFOLG] Zug {zug.zug_nummer} wurde automatisch abgefahren. "
                  f"Gleis {gleis.gleis_nummer} schon freigegeben!")

            return f"Der Zug wurde {zug.zug_nummer} abgefahren!"

    except Fahrstrasse.DoesNotExist:
        print(f"[❌ FEHLER] Fahrstraße ID {fahrstrasse_id} nicht in der Datenbank gefunden.")
        return "Fahrstraße nicht gefunden"