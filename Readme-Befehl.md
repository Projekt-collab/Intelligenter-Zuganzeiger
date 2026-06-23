# 🚀 Projekt starten

## 1. Container bauen und starten
docker compose up -d --build

## 2. Datenbank einrichten (Migrationen ausführen)
docker compose exec web python manage.py migrate

## 3. Admin-Nutzer erstellen
docker compose exec web python manage.py createsuperuser

---

# 🛠️ Wichtige Befehle für die Entwicklung
Da das Projekt komplett in Docker läuft, müssen alle Django-Befehle im Kontext des Containers ausgeführt werden:

* **Neue App erstellen:**
  docker compose exec web python manage.py startapp <app_name>

* **Neue Migrationen erstellen (nach Model-Änderungen):**
  docker compose exec web python manage.py makemigrations