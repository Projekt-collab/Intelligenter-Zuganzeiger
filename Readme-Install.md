# Intelligenter Zuganzeiger 🚄

## 🛠️ Schnellstart-Anleitung (Windows & Docker)


# 1. Repository klonen und in den Ordner wechseln
```powershell
git clone [https://github.com/Projekt-collab/Intelligenter-Zuganzeiger.git](https://github.com/Projekt-collab/Intelligenter-Zuganzeiger.git)
```


```powershell
cd Intelligenter-Zuganzeiger
```

# 2. Docker-Container bauen und starten
```powershell
docker compose up --build
```

# 3. Datenbank-Migrationen im Container ausführen
```powershell
docker compose exec web python manage.py migrate
```


# 4. Standard-Daten (Fixtures) in die Datenbank laden
```powershell
docker compose exec web python manage.py loaddata default_data
```