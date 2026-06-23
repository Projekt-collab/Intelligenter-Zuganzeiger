# 🌿 Git Flow Entwicklungsleitfaden

Dieses Dokument beschreibt den Git-Flow-Workflow für unser Stellwerk-Projekt. Bitte halte dich strikt an diese Struktur, um einen sauberen Quellcode-Verlauf zu garantieren und Konflikte zu vermeiden.

---

## 🏗️ Das Branch-Modell

* **`main`**: Enthält den stabilen, produktionsbereiten Code. Hier wird niemals direkt gearbeitet.
* **`feature/*`**: Zweige für neue Funktionen, Bugfixes oder Aufgaben. Sie zweigen von `main` ab und fließen über einen Pull Request wieder dorthin zurück.

---

## 🔄 Der Entwicklungs-Prozess (Schritt für Schritt)

### 1. Vorbereitung & Aktualisierung
Bevor du ein neues Feature beginnst, bringe deinen lokalen Stand auf den neuesten Stand des Servers.

```bash
# Auf den Hauptzweig wechseln
git checkout main

# Neueste Änderungen vom Server herunterladen
git pull origin main
```

### 2. Erstellt den Branch und wechselt sofort dorthin
```bash
git checkout -b feature/stellwerk-logik
```

### 3. Änderungen committen
```bash
# Geänderte Dateien für den Commit markieren
git add .

# Aussagekräftige Commit-Nachricht schreiben (Nutze 'feat:' oder 'fix:')
git commit -m "feat: Kollisionserkennung über UniqueConstraint hinzugefügt"
```
### 4. Branch auf den GitHub pushen
```bash
git push origin feature/stellwerk-logik
```

### 5. Pull Request (PR) erstellen
* Öffne das Projekt im Browser auf der Git-Plattform.
* Klicke auf den Button "Create Pull Request" für deinen gerade gepushten Branch.
* Wichtig in der Beschreibung: Erwähne kurz, was geändert wurde und ob das Team nach dem Pullen neue Datenbank-Migrationen (docker compose exec web python manage.py migrate) ausführen muss!

### 6. Code Review & Mergen
* Review: Mindestens ein anderes Teammitglied überprüft den Code auf Fehler und Logik.
* Merge: Nach der Freigabe wird der Pull Request auf der Plattform in den main-Branch gemergt.
* Lokales Aufräumen: Du kannst den alten Zweig nun lokal löschen:
```bash
git checkout main
git pull
git branch -d feature/stellwerk-logik
```