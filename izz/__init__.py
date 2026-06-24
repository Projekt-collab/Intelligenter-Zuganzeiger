from .celery import app as celery_app

# Das sorgt dafür, dass die App immer geladen wird, wenn Django startet.
__all__ = ('celery_app',)