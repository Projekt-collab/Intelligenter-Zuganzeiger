import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StellwerkConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Name der Gruppe (alle Stellwerke/Züge hören im selben 'Funkkanal')
        self.room_group_name = 'stellwerk_channel'

        # Verbindung akzeptieren
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print("🟢 Ein Zug hat sich via WebSocket verbunden!")

    async def disconnect(self, close_code):
        # Verbindung trennen
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print("🔴 Verbindung zu Zug getrennt.")

    # 1. Nachricht kommt VOM ZUG (Client -> Server)
    async def receive(self, text_data):
        data = json.loads(text_data)
        nachrichten_typ = data.get('type')
        zug_nummer = data.get('zug_nummer')

        print(f"📡 Nachricht erhalten von {zug_nummer}: {nachrichten_typ}")

        if nachrichten_typ == 'einfahrt_anfrage':
            # Hier senden wir die Nachricht an das gesamte Stellwerk-Netzwerk
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'stellwerk_nachricht', # Ruft die unten stehende Methode auf
                    'message': f"Zug {zug_nummer} bittet um Einfahrt!"
                }
            )

    # 2. Nachricht geht AN DEN ZUG (Server -> Client)
    async def stellwerk_nachricht(self, event):
        message = event['message']

        # Sende die Nachricht über das WebSocket-Protokoll an die Lok/Front-End
        await self.send(text_data=json.dumps({
            'status': 'update',
            'message': message
        }))