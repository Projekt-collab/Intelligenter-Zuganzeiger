# Intelligenter-Zuganzeiger
Echtzeit-Stellwerk-Steuerung mit Django, Redis und WebSockets
# 1. Virtuelle Umgebung erstellen (nur einmalig nötig)
python -m venv venv
# 2. Umgebung aktivieren
# Unter Windows (Command Prompt):
venv\Scripts\activate
# Unter Windows (PowerShell):
.\venv\Scripts\activate
# 3. Dependencies installieren
pip install -r requires.txt
# 4. Neue App erstellen
py manage.py startapp <app_name>
# Wir fügen (docker compose exec web) für jeden Befehl hinzu, damit wir in docker kontext arbeiten können
# 5. Neue Migration erstellen
docker compose exec web python manage.py makemigrations
# 6. Migrationen ausführen
docker compose exec web python manage.py migrate
# 7. Admin-Nutzer erstellen
docker compose exec web python manage.py createsuperuser