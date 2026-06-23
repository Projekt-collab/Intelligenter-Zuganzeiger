import pymysql
from .celery import app as celery_app

pymysql.install_as_MySQLdb()

# Das sorgt dafür, dass die App immer geladen wird, wenn Django startet.
__all__ = ('celery_app',)