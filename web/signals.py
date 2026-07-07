from django.db.models.signals import post_save
from django.dispatch import receiver
from web.models import Fahrstrasse
from web.tasks import gleis_automatisch_freigeben


@receiver(post_save, sender=Fahrstrasse)
def fahrstrasse_erstellt_trigger(sender, instance, created, **kwargs):
    if created and instance.ist_aktiv:
        print(f"[DJANGO SIGNAL] Zug {instance.zug.zug_nummer} hat die Fahrstraße besetzt. "
              f"Automatische Abfahrt in 2 Minuten geplant...")

        gleis_automatisch_freigeben.apply_async(
            args=[instance.id],
            countdown=120
        )