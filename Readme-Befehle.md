# 🚀 Projekt starten

## 1. Container bauen und starten
```bash
docker compose up -d --build
```

## 2. Datenbank einrichten (Migrationen ausführen)
```bash
docker compose exec web python manage.py migrate
```

## 3. Admin-Nutzer erstellen
```bash
docker compose exec web python manage.py createsuperuser
```

## 4. Fixtures loaden
```bash
docker compose exec web python manage.py loaddata default_data
```

# 🛠️ Wichtige Befehle für die Entwicklung
Da das Projekt komplett in Docker läuft, müssen alle Django-Befehle im Kontext des Containers ausgeführt werden:

* **Neue App erstellen:**
```bash
  docker compose exec web python manage.py startapp <app_name>
```
* **Neue Migrationen erstellen (nach Model-Änderungen):**
```bash
  docker compose exec web python manage.py makemigrations
```

* **Static Dateien generiert**
```bash
  docker-compose exec web python manage.py collectstatic --noinput
```