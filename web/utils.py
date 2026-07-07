from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import StellwerkAnfrage, Gleis, Fahrstrasse


def send_stellwerk_update(log_message: str):
    channel_layer = get_channel_layer()

    anfragen = StellwerkAnfrage.objects.filter(ergebnis='OFFEN')
    anfragen_list = [{'zug_nummer': a.zug.zug_nummer} for a in anfragen]

    gleise_liste = []
    for g in Gleis.objects.all():
        aktive_res = Fahrstrasse.objects.filter(gleis=g, ist_aktiv=True).select_related('zug').first()
        gleise_liste.append({
            'gleis_nummer': g.gleis_nummer,
            'sensor_belegt': g.sensor_belegt,
            'zug': aktive_res.zug.zug_nummer if aktive_res else None
        })

    aktueller_zustand = {
        'anfragen': anfragen_list,
        'gleise': gleise_liste
    }

    async_to_sync(channel_layer.group_send)(
        'stellwerk_dispatcher',
        {
            'type': 'stellwerk_update_event',
            'data': aktueller_zustand,
            'log_message': log_message
        }
    )


def send_zug_redirect(zug_nummer: str):
    channel_layer = get_channel_layer()

    group_name = f"zug_{zug_nummer.replace(' ', '_')}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "zug_befehl",
            "message": "redirect_to_dashboard"
        }
    )