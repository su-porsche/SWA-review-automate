# 🚀 Quick Reference - Migration auf neuen Rechner

**Schnellreferenz für die Übertragung des MPC-Projekts**

---

## 📦 Backup erstellen (Alter Rechner)

```bash
cd /mnt/c/Users/[USERNAME]/OneDrive*/MPC

# Automatisches Backup erstellen
./scripts/backup_for_migration.sh

# Backup-Verzeichnis: ./backups/[DATUM]/
```

**Was wird gesichert:**
- ✅ Komplettes Projekt-Archiv (tar.gz)
- ✅ Datenbank-Backup (SQL)
- ✅ VS Code Extensions-Liste
- ✅ WSL-Konfiguration
- ✅ Umgebungsinformationen
- ✅ CA-Zertifikat

---

## 💾 Dateien übertragen

### Option A: OneDrive (empfohlen)
- Projekt liegt bereits in OneDrive
- Automatische Synchronisierung
- Auf neuem Rechner: OneDrive abwarten

### Option B: USB/Netzwerk
```bash
# Backup-Ordner kopieren
cp -r backups/[DATUM] /mnt/d/backup_mpc/

# Auf neuem Rechner einfügen
```

---

## 🖥️ Neuer Rechner - Setup

### 1. WSL2 installieren (Windows PowerShell als Admin)
```powershell
wsl --install -d Ubuntu-24.04
wsl --set-default-version 2
```

### 2. WSL konfigurieren
```bash
# /etc/wsl.conf erstellen
sudo nano /etc/wsl.conf
```

Inhalt:
```ini
[boot]
systemd=true

[automount]
enabled=true
```

WSL neu starten (PowerShell):
```powershell
wsl --shutdown
wsl
```

### 3. Docker installieren
```bash
# Docker Repository
sudo apt update
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker installieren
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Docker-Gruppe
sudo usermod -aG docker $USER

# WSL neu starten!
exit
wsl
```

### 4. CA-Zertifikat installieren
```bash
cd ~/MPC  # oder OneDrive-Pfad

sudo cp PAG-Interception-CA-ROOT-01.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

### 5. Automatisches Setup
```bash
cd ~/MPC  # oder OneDrive-Pfad

# Alles automatisch installieren
./scripts/setup_wsl_complete.sh
```

**Oder manuell:**
```bash
# Python Virtual Environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Docker starten
docker compose up -d db

# Datenbank initialisieren
docker exec -i mpc-db-1 psql -U postgres -d mpc_db < sql/create_knowledgebase.sql

# ODER aus Backup
cat backup_mpc_db_*.sql | docker exec -i mpc-db-1 psql -U postgres -d mpc_db
```

### 6. VS Code installieren
```bash
# Windows: VS Code installieren
# Download: https://code.visualstudio.com/

# WSL Extension installieren (in VS Code)

# Projekt in WSL öffnen
code .
```

### 7. VS Code Extensions installieren
```bash
# Automatisch aus Liste
cat vscode_extensions_wsl.txt | xargs -L 1 code --install-extension

# Oder manuell (wichtigste):
code --install-extension ms-ossdata.vscode-pgsql
code --install-extension github.copilot
code --install-extension github.copilot-chat
code --install-extension ms-python.python
```

---

## ✅ Verifikation

```bash
# System prüfen
wsl --status                    # WSL2 aktiv
python3 --version              # Python 3.12.x
docker --version               # Docker 28.x
docker ps                      # Container laufen

# Projekt prüfen
source .venv/bin/activate
python src/view_db.py         # Datenbank anzeigen
ls data/pdfs/                 # PDFs vorhanden (4 Dateien)

# VS Code
code --version
code .                        # Projekt öffnen
```

---

## 🔧 Wichtige Befehle

### WSL
```bash
wsl --shutdown               # WSL komplett stoppen
wsl --list --verbose        # WSL-Distributionen anzeigen
wsl --status                # WSL-Status
```

### Docker
```bash
docker compose up -d        # Container starten
docker compose down         # Container stoppen
docker compose logs db      # Logs anzeigen
docker ps                   # Laufende Container
docker exec -it mpc-db-1 psql -U postgres -d mpc_db  # In DB einloggen
```

### Python
```bash
source .venv/bin/activate   # Virtual Env aktivieren
deactivate                  # Virtual Env deaktivieren
pip list                    # Installierte Pakete
pip install -r requirements.txt  # Pakete installieren
```

### Git (falls verwendet)
```bash
git config --global user.name "Name"
git config --global user.email "email@porsche.de"
git status
git pull
git push
```

---

## 🐛 Häufige Probleme

### Docker startet nicht
```bash
sudo systemctl start docker
sudo systemctl status docker
```

### Permission denied bei Docker
```bash
sudo usermod -aG docker $USER
# Dann WSL neu starten
```

### Python-Pakete Installation schlägt fehl
```bash
sudo apt install -y python3-dev build-essential libpq-dev
pip install -r requirements.txt
```

### CA-Zertifikat Probleme
```bash
sudo update-ca-certificates --fresh
```

### WSL zu langsam
`.wslconfig` in Windows erstellen (`C:\Users\[USERNAME]\.wslconfig`):
```ini
[wsl2]
memory=8GB
processors=4
```

---

## 📁 Wichtige Dateien & Pfade

### Projekt
```
/mnt/c/Users/[USERNAME]/OneDrive - Dr. Ing. h.c. F. Porsche AG/Notebooks/Projects/AI/Arch_review/POC/MPC
```

### Konfigurationen
```
/etc/wsl.conf               # WSL-Konfiguration
~/.bashrc                   # Bash-Konfiguration
~/.gitconfig                # Git-Konfiguration
```

### CA-Zertifikat
```
/usr/local/share/ca-certificates/PAG-Interception-CA-ROOT-01.crt
```

### VS Code
```
~/.vscode-server/           # VS Code Server in WSL
```

---

## 📚 Dokumentation

- **Vollständige Anleitung:** [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- **WSL & VS Code Setup:** [WSL_VSCODE_SETUP.md](WSL_VSCODE_SETUP.md)
- **Projekt-Readme:** [README.md](README.md)
- **Quick Start:** [docs/QUICK_START.md](docs/QUICK_START.md)

---

## ⏱️ Geschätzte Zeiten

| Schritt | Zeit |
|---------|------|
| WSL2 Installation | 10-15 min |
| Docker Installation | 5-10 min |
| Projekt Setup | 5 min |
| Datenübertragung (OneDrive) | Automatisch |
| Datenübertragung (USB) | 1-2 min |
| **Gesamt** | **30-45 min** |

---

**Stand:** Februar 2026  
**Für Fragen:** Siehe vollständige Dokumentation
