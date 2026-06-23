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
python manage.py startapp <app_name>

# 5. Neue Migration erstellen
python manage.py makemigrations

# 6. Migrationen ausführen
python manage.py migrate

# 7. Admin-Nutzer erstellen
python manage.py createsuperuser