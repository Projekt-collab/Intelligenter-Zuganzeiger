import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from web.models import Fahrt, Gleis, Fahrstrasse, StellwerkAnfrage


class StellwerkConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.reject()
            return

        # 1. Fall: Der User ist ein Dispatcher
        ist_dispatcher = await self.check_group(user, 'Dispatcher')
        if ist_dispatcher:
            self.room_group_name = 'stellwerk_dispatcher'
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            print(f"🟢 Dispatcher {user} verbunden.")
            return

        # 2. Fall: Der User ist ein Lokführer, dann holt den aktiven Zug
        zug = await self.get_aktiven_zug_fuer_user(user)

        if zug:
            self.room_group_name = f"zug_{zug.zug_nummer.replace(' ', '_')}"
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            print(f"🚂 Lokführer {user} für {zug.zug_nummer} verbunden.")
        else:
            self.room_group_name = None
            await self.accept()
            print(f"🟡 Lokführer {user} ohne aktiven Zug verbunden.")

    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print("🔴 Verbindung getrennt.")

    async def receive(self, text_data):
        data = json.loads(text_data)
        nachrichten_typ = data.get('type')
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.send(text_data=json.dumps({'status': 'error', 'message': 'Nicht eingeloggt!'}))
            return

        # Lokführer brauchen zwingend einen aktiven Zug.
        zug = None
        ist_dispatcher = await self.check_group(user, 'Dispatcher')
        if not ist_dispatcher:
            zug = await self.get_aktiven_zug_fuer_user(user)
            if not zug:
                await self.send(text_data=json.dumps({'status': 'error', 'message': 'Keine aktive Fahrt gefunden.'}))
                return

        # --- FALL 1: EINFAHRT ANFRAGEN (Lokführer) ---
        if nachrichten_typ == 'einfahrt_anfrage' and zug:
            gleis_reserviert, info_nachricht = await self.versuche_gleis_reservierung(zug)

            # 1. Antwort direkt an den Lokführer schicken
            await self.send(text_data=json.dumps({'status': 'update', 'message': info_nachricht}))

            # 2. Update an ALLE Dispatcher in der Gruppe senden
            aktueller_zustand = await self.get_stellwerk_zustand()
            await self.channel_layer.group_send(
                'stellwerk_dispatcher',
                {
                    'type': 'stellwerk.update.event',  # Channels konvertiert Punkte zu Unterstrichen
                    'data': aktueller_zustand,
                    'log_message': f"📢 {zug.zug_nummer}: {info_nachricht}"
                }
            )

        # --- FALL 2: ZUG FÄHRT LOS (Lokführer) ---
        elif nachrichten_typ == 'zug_faehrt_los' and zug:
            erfolg, info_nachricht, gleis = await self.belege_gleis_fuer_zug(zug)
            if erfolg:
                # 1. Antwort direkt an den Lokführer schicken
                await self.send(text_data=json.dumps({'status': 'update', 'message': info_nachricht, 'gleis': gleis}))

                # 2. Update an ALLE Dispatcher in der Gruppe senden
                aktueller_zustand = await self.get_stellwerk_zustand()
                await self.channel_layer.group_send(
                    'stellwerk_dispatcher',
                    {
                        'type': 'stellwerk.update.event',
                        'data': aktueller_zustand,
                        'log_message': f"🚨 {zug.zug_nummer}: {info_nachricht}"
                    }
                )
            else:
                await self.send(text_data=json.dumps({'status': 'error', 'message': info_nachricht}))

    # Diese Methode MUSS exakt so heißen, damit sie das Gruppen-Event empfängt
    async def stellwerk_update_event(self, event):
        """Wird aufgerufen, wenn ein Event an 'stellwerk_dispatcher' gesendet wird"""
        await self.send(text_data=json.dumps({
            'type': 'system_update',
            'data': event['data'],
            'message': event['log_message']
        }))

    async def zug_befehl(self, event):
        await self.send(text_data=json.dumps({
            'status': 'befehl',
            'message': event['message']
        }))

    # =========================================================================
    #  🛑 DATENBANK-METHODEN (MÜSSEN INNERHALB DER KLASSE SEIN, 4 LEERZEICHEN EINRÜCKUNG)
    # =========================================================================

    @database_sync_to_async
    def check_group(self, user, group_name):
        """Prüft synchron in der DB, ob der User in der Gruppe 'Dispatcher' ist"""
        return user.groups.filter(name=group_name).exists()

    @database_sync_to_async
    def get_aktiven_zug_fuer_user(self, user):
        """Findet den Zug, den der Lokführer gerade aktiv fährt"""
        fahrt = Fahrt.objects.filter(lokfuehrer=user, fahrt_ende__isnull=True).first()

        return fahrt.zug if fahrt else None

    @database_sync_to_async
    def get_stellwerk_zustand(self):
        """Generiert den aktuellen Zustand für das dispatcher.html Template"""
        anfragen = StellwerkAnfrage.objects.filter(ergebnis='GENEHMIGT').select_related('zug')
        anfragen_list = [{'zug_nummer': a.zug.zug_nummer} for a in anfragen]

        gleise_liste = []
        for g in Gleis.objects.all():
            aktive_fahrstrasse = Fahrstrasse.objects.filter(gleis=g, ist_aktiv=True).select_related('zug').first()
            gleise_liste.append({
                'gleis_nummer': g.gleis_nummer,
                'sensor_belegt': g.sensor_belegt,
                'zug': aktive_fahrstrasse.zug.zug_nummer if aktive_fahrstrasse else None
            })

        return {
            'anfragen': anfragen_list,
            'gleise': gleise_liste
        }

    @database_sync_to_async
    def versuche_gleis_reservierung(self, zug):
        """Sucht nach freien Gleisen und reserviert eins im Transaktionsblock mit Zeilensperre"""
        try:
            with transaction.atomic():
                # Prüfen, ob der Zug bereits ein Gleis reserviert hat
                bereits_reserviert = StellwerkAnfrage.objects.filter(
                    zug=zug,
                    ergebnis='GENEHMIGT',
                    zugewiesenes_gleis__isnull=False
                ).first()

                if bereits_reserviert:
                    # Der Lokführer fragt noch einmal, hat aber schon ein Gleis!
                    gleis_nummer = bereits_reserviert.zugewiesenes_gleis.gleis_nummer
                    return False, f"Du hast bereits eine Freigabe! Einfahrt erlaubt auf Gleis {gleis_nummer}."
                # Verhindert, dass zwei Züge gleichzeitig dasselbe freie Gleis sehen
                anfrage = StellwerkAnfrage.objects.create(zug=zug, ergebnis='OFFEN')

                # Finde ein Gleis, das weder physisch belegt noch aktiv reserviert ist
                freies_gleis = Gleis.objects.filter(
                    sensor_belegt=False
                ).exclude(
                    reservierungen__ist_aktiv=True
                ).select_for_update().first()

                if freies_gleis:
                    # Fahrstraße exakt für dieses Gleis erstellen
                    Fahrstrasse.objects.create(zug=zug, gleis=freies_gleis, ist_aktiv=True)

                    anfrage.ergebnis = 'GENEHMIGT'
                    anfrage.zugewiesenes_gleis = freies_gleis
                    anfrage.save()

                    zug.status = 'FAHRT'
                    zug.save()

                    return True, f"Einfahrt erlaubt auf Gleis {freies_gleis.gleis_nummer}!"
                else:
                    anfrage.ergebnis = 'ABGEWIESEN'
                    anfrage.save()

                    return False, "Kein Gleis frei. Bitte warten am Einfahrtssignal!"
        except Exception as e:
            print(f"Datenbankfehler bei der Reservierung: {e}")

            return False, "Systemfehler bei der Gleissuche."

    @database_sync_to_async
    def belege_gleis_fuer_zug(self, zug):
        """Aktiviert den Sensor des EXAKT reservierten Gleises"""
        try:
            with transaction.atomic():
                # Hole die exakt für diesen Zug aktivierte Fahrstraße
                fahrstrasse = Fahrstrasse.objects.filter(zug=zug, ist_aktiv=True).select_related('gleis').first()
                anfrage = StellwerkAnfrage.objects.filter(
                    zug=zug,
                    ergebnis='GENEHMIGT',
                    zugewiesenes_gleis__isnull=False
                ).first()
                if not fahrstrasse:
                    return False, "Du hast noch keine Fahrstraßen-Freigabe!"

                gleis = fahrstrasse.gleis
                gleis.sensor_belegt = True
                gleis.save()

                if anfrage:
                    anfrage.ergebnis = 'BEENDEN'
                    anfrage.save()

                zug.status = 'GEPARKT'
                zug.save()

                return True, f"Gleis {gleis.gleis_nummer} erfolgreich besetzt!", gleis.gleis_nummer
        except Exception as e:
            print(f"Fehler beim Einfahren: {e}")

            return False, "Systemfehler beim Einfahrvorgang."