# 1. Virtuelle Umgebung erstellen (nur einmalig nötig)
python -m venv venv

# 2. Umgebung aktivieren
# Unter Windows (Command Prompt):
venv\Scripts\activate
# Unter Windows (PowerShell):
.\venv\Scripts\activate
# Unter Mac/Linux:
source venv/bin/activate

# 3. Dependencies installieren
pip install -r requires.txt