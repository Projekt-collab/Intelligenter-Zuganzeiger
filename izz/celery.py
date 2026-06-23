import os
from celery import Celery

# Setze das Standard-Django-Einstellungsmodul für das 'celery'-Programm.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'izz.settings')

# Erstelle die Celery-App (der Name 'izz' sollte deinem Ordnernamen entsprechen)
app = Celery('izz')

# Hier sagen wir Celery, dass es seine Konfiguration direkt aus den Django-Settings lesen soll.
# Der Namespace 'CELERY' bedeutet, dass alle Celery-Konfigurationen in der settings.py mit 'CELERY_' beginnen müssen.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Celery sucht automatisch nach 'tasks.py'-Dateien in all deinen installierten Django-Apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')