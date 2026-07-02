import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from web.models import Zug, Fahrt, Gleis, Fahrstrasse, StellwerkAnfrage


class StellwerkConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'stellwerk_channel'

        # Verbindung zum Channel-Layer hinzufügen
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"🟢 User {self.scope['user']} hat sich via WebSocket verbunden!")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print("🔴 Verbindung getrennt.")

    # Nachricht kommt VOM CLIENT (Lokführer drückt den Button)
    async def receive(self, text_data):
        data = json.loads(text_data)
        nachrichten_typ = data.get('type')
        user = self.scope["user"]

        # Anonyme User abfangen
        if not user.is_authenticated:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': 'Fehler: Du bist nicht eingeloggt!'
            }))
            return

        if nachrichten_typ == 'einfahrt_anfrage':
            # 1. Zug des Lokführers ermitteln
            zug = await self.get_aktiven_zug_fuer_user(user)
            if not zug:
                await self.send(text_data=json.dumps({
                    'status': 'error',
                    'message': 'Fehler: Du hast aktuell keine aktive Fahrt!'
                }))
                return

            # 2. Versuchen, ein freies Gleis zu finden und zu reservieren
            gleis_reserviert, info_nachricht = await self.versuche_gleis_reservierung(zug)

            if gleis_reserviert:
                # Erfolg! Wir benachrichtigen speziell DIESEN Zug
                await self.send(text_data=json.dumps({
                    'status': 'update',
                    'message': info_nachricht
                }))
                # Optional: Das gesamte Stellwerk-Netzwerk informieren, dass ein Gleis belegt wurde
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'stellwerk_nachricht',
                        'message': f"📢 {zug.zug_nummer} fahrplanmäßig auf {info_nachricht}"
                    }
                )
            else:
                # Kein Gleis frei: Dem Zug sagen, dass er warten muss
                await self.send(text_data=json.dumps({
                    'status': 'update',
                    'message': info_nachricht  # "Kein Gleis frei. Bitte warten..."
                }))
        elif nachrichten_typ == 'zug_faehrt_los':
            zug = await self.get_aktiven_zug_fuer_user(user)
            if not zug:
                await self.send(text_data=json.dumps({'status': 'error', 'message': 'Keine aktive Fahrt gefunden.'}))
                return

            # Gleis belegen und Status updaten
            erfolg, info_nachricht = await self.belege_gleis_fuer_zug(zug)

            if erfolg:
                # Dem Lokführer den Erfolg melden
                await self.send(text_data=json.dumps({
                    'status': 'update',
                    'message': info_nachricht
                }))
                # Das gesamte Stellwerk informieren (z.B. für Stellwerks-Monitore)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'stellwerk_nachricht',
                        'message': f"🚨 {zug.zug_nummer} ist jetzt auf {info_nachricht}"
                    }
                )
            else:
                await self.send(text_data=json.dumps({
                    'status': 'error',
                    'message': info_nachricht
                }))

    # Nachricht vom Channel-Layer (geht an alle im Kanal)
    async def stellwerk_nachricht(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'status': 'update',
            'message': message
        }))

    # --- DATENBANK HELFER-METHODEN ---

    @database_sync_to_async
    def get_aktiven_zug_fuer_user(self, user):
        """Findet den Zug, den der Lokführer gerade aktiv fährt"""
        fahrt = Fahrt.objects.filter(lokfuehrer=user, fahrt_ende__isnull=True).first()
        return fahrt.zug if fahrt else None

    @database_sync_to_async
    def versuche_gleis_reservierung(self, zug):
        """Sucht nach freien Gleisen und reserviert eins im Transaktionsblock"""
        try:
            with transaction.atomic():
                # Erstelle zuerst einen Stellwerk-Eintrag (Protokoll)
                anfrage = StellwerkAnfrage.objects.create(zug=zug, ergebnis='OFFEN')

                # Finde alle Gleise, die NICHT per Sensor belegt sind
                # UND keine aktive Fahrstraßen-Reservierung haben
                freies_gleis = Gleis.objects.filter(
                    sensor_belegt=False
                ).exclude(
                    reservierungen__ist_aktiv=True
                ).first()

                if freies_gleis:
                    # Fahrstraße anlegen (Reservierung)
                    Fahrstrasse.objects.create(zug=zug, gleis=freies_gleis, ist_aktiv=True)

                    # Anfrage-Modell aktualisieren
                    anfrage.ergebnis = 'GENEHMIGT'
                    anfrage.zugewiesenes_gleis = freies_gleis
                    anfrage.save()

                    # Zug-Status ändern
                    zug.status = 'FAHRT'
                    zug.save()

                    return True, f"Einfahrt erlaubt auf Gleis {freies_gleis.gleis_nummer}!"

                else:
                    # Kein Gleis frei
                    anfrage.ergebnis = 'ABGEWIESEN'
                    anfrage.save()
                    return False, "Kein Gleis frei. Bitte warten am Einfahrtssignal!"

        except Exception as e:
            print(f"Datenbankfehler bei der Reservierung: {e}")
            return False, "Systemfehler bei der Gleissuche."

    @database_sync_to_async
    def belege_gleis_fuer_zug(self, zug):
        """Aktiviert den physischen Sensor des zugewiesenen Gleises"""
        try:
            with transaction.atomic():
                # Finde die aktive Fahrstraße für diesen Zug
                fahrstrasse = Fahrstrasse.objects.filter(zug=zug, ist_aktiv=True).first()

                if not fahrstrasse:
                    return False, "Du hast noch keine Fahrstraßen-Freigabe! Bitte zuerst Gleis anfordern."

                # Hol das Gleis aus der Reservierung
                gleis = fahrstrasse.gleis

                # Physischen Sensor auf belegt setzen
                gleis.sensor_belegt = True
                gleis.save()

                # Status des Zuges ändern (Er steht jetzt am Gleis im Bahnhof)
                zug.status = 'GEPARKT'
                zug.save()

                return True, f"Gleis {gleis.gleis_nummer} erfolgreich besetzt!"

        except Exception as e:
            print(f"Fehler beim Einfahren: {e}")
            return False, "Systemfehler beim Einfahrvorgang."