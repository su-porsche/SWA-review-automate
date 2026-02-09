# 🖥️ WSL & VS Code Setup-Dokumentation für Migration

**Projekt:** MPC - PDF to Knowledge Base System  
**Datum:** 9. Februar 2026  
**System:** WSL2 Ubuntu 24.04 + VS Code Remote

---

## 📋 Übersicht

Dieses Dokument beschreibt die vollständige WSL- und VS Code-Konfiguration für das MPC-Projekt und wie diese auf einem neuen Rechner eingerichtet wird.

---

## 🔍 Aktuelle Konfiguration (IT223434)

### WSL-Umgebung
- **WSL Version:** WSL2
- **Distribution:** Ubuntu 24.04
- **systemd:** Aktiviert
- **Automount:** Aktiviert (`/mnt/c/...`)

### Installierte Software
- **Python:** 3.12.3
- **pip:** 24.0
- **Docker:** 28.5.1
- **Docker Compose:** v2.40.2
- **PostgreSQL:** 16 (Client & Server)
- **Git:** Installiert

### VS Code
- **Workspace:** POC.code-workspace (Multi-Folder)
- **VS Code Remote Server:** Installiert in WSL

### VS Code Extensions (WSL)
```
anthropic.claude-code
ckolkman.vscode-postgres
cweijan.dbclient-jdbc
cweijan.vscode-postgresql-client2
github.copilot
github.copilot-chat
ms-ossdata.vscode-pgsql
ms-vscode.cmake-tools
ms-vscode.cpptools
ms-vscode.cpptools-extension-pack
openai.chatgpt
```

### Sicherheit & Netzwerk
- **Porsche CA-Zertifikat:** PAG-Interception-CA-ROOT-01.crt
  - Installiert unter: `/usr/local/share/ca-certificates/`
  - Gültig bis: 31. Dezember 2025
  - Zweck: Corporate Network Interception/SSL-Inspection

---

## 🔧 Setup-Anleitung für neuen Rechner

### Phase 1: WSL2 Installation
<details>
<summary>📋 WSL2 Grundinstallation (Windows)</summary>

#### 1.1 WSL2 aktivieren (PowerShell als Administrator)
```powershell
# WSL Feature aktivieren
wsl --install

# ODER manuell:
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Neustart erforderlich
Restart-Computer
```

#### 1.2 WSL2 als Standard setzen
```powershell
wsl --set-default-version 2
```

#### 1.3 Ubuntu 24.04 installieren
```powershell
# Ubuntu 24.04 aus Microsoft Store installieren
wsl --install -d Ubuntu-24.04

# ODER manuell:
# Download von Microsoft Store: "Ubuntu 24.04 LTS"
```

#### 1.4 WSL starten und Benutzer einrichten
```bash
# Beim ersten Start: Benutzername und Passwort eingeben
# Empfohlen: Gleicher Benutzername wie Windows
```

</details>

### Phase 2: WSL-Konfiguration
<details>
<summary>⚙️ Systemkonfiguration</summary>

#### 2.1 WSL-Konfigurationsdatei erstellen
```bash
sudo nano /etc/wsl.conf
```

Inhalt:
```ini
[network]
generateResolvConf=true
generateHosts=true

[boot]
systemd=true

[automount]
enabled=true
root=/mnt/
options="metadata,umask=22,fmask=11"

[interop]
enabled=true
appendWindowsPath=true
```

**Bedeutung:**
- `systemd=true`: Systemd für Dienstverwaltung (Docker benötigt dies)
- `automount`: Windows-Laufwerke unter `/mnt/c/` verfügbar
- `appendWindowsPath`: Windows-Befehle in WSL nutzbar

#### 2.2 WSL neu starten (Windows PowerShell)
```powershell
wsl --shutdown
wsl
```

#### 2.3 System aktualisieren
```bash
sudo apt update
sudo apt upgrade -y
```

</details>

### Phase 3: Porsche CA-Zertifikat installieren
<details>
<summary>🔐 SSL-Zertifikat für Corporate Network</summary>

#### 3.1 Zertifikat kopieren
```bash
# Zertifikat von Windows nach WSL kopieren (falls im Projekt)
sudo cp /mnt/c/Users/[USERNAME]/OneDrive*/MPC/PAG-Interception-CA-ROOT-01.crt \
        /usr/local/share/ca-certificates/

# ODER direkt vom Backup
sudo cp ~/MPC/PAG-Interception-CA-ROOT-01.crt \
        /usr/local/share/ca-certificates/
```

#### 3.2 Berechtigungen setzen
```bash
sudo chmod 644 /usr/local/share/ca-certificates/PAG-Interception-CA-ROOT-01.crt
```

#### 3.3 Zertifikat aktivieren
```bash
sudo update-ca-certificates
```

**Ausgabe sollte sein:**
```
Updating certificates in /etc/ssl/certs...
1 added, 0 removed; done.
```

#### 3.4 Für Python pip konfigurieren (optional)
```bash
# Falls pip Zertifikat-Probleme hat:
pip config set global.cert /etc/ssl/certs/ca-certificates.crt
```

#### 3.5 Für Git konfigurieren (optional)
```bash
git config --global http.sslCAInfo /usr/local/share/ca-certificates/PAG-Interception-CA-ROOT-01.crt
```

</details>

### Phase 4: Software installieren
<details>
<summary>📦 Python, Docker, Git & Tools</summary>

#### 4.1 Python 3.12 (sollte bereits vorhanden sein)
```bash
python3 --version  # Sollte 3.12.x zeigen

# Falls nicht installiert:
sudo apt install -y python3 python3-pip python3-venv

# Development-Pakete (für C-Extensions)
sudo apt install -y python3-dev build-essential
```

#### 4.2 Git
```bash
sudo apt install -y git

# Git-Konfiguration
git config --global user.name "Ihr Name"
git config --global user.email "ihre.email@porsche.de"
```

#### 4.3 Docker installieren
```bash
# Docker's offizielle GPG-Key hinzufügen
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Docker Repository hinzufügen
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker installieren
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Docker-Dienst starten
sudo systemctl enable docker
sudo systemctl start docker

# Aktuellen Benutzer zur Docker-Gruppe hinzufügen
sudo usermod -aG docker $USER

# WICHTIG: WSL neu starten oder neu einloggen
exit
wsl
```

#### 4.4 Docker testen
```bash
docker --version
docker compose version
docker run hello-world
```

#### 4.5 PostgreSQL Client (optional, für lokale DB-Verwaltung)
```bash
sudo apt install -y postgresql-client-16

# Test
psql --version
```

#### 4.6 Nützliche Tools
```bash
# Entwickler-Tools
sudo apt install -y curl wget vim nano tree htop

# PDF-Processing-Tools (für PyMuPDF/pdfplumber)
sudo apt install -y tesseract-ocr tesseract-ocr-deu

# Kompressionstools
sudo apt install -y zip unzip tar gzip
```

</details>

### Phase 5: VS Code & Extensions
<details>
<summary>🔧 Visual Studio Code Setup</summary>

#### 5.1 VS Code auf Windows installieren
- Download: https://code.visualstudio.com/
- Während der Installation: **Alle Optionen** aktivieren
  - ✅ Add "Open with Code" to context menu
  - ✅ Add to PATH

#### 5.2 WSL Extension installieren
1. VS Code öffnen
2. Extensions (Strg+Shift+X)
3. Suchen: "WSL"
4. Installieren: **"WSL" von Microsoft**

#### 5.3 VS Code in WSL öffnen
```bash
# In WSL, im Projekt-Verzeichnis:
cd /mnt/c/Users/[USERNAME]/OneDrive*/MPC
code .
```

Beim ersten Mal:
- VS Code Server wird automatisch in WSL installiert
- Extensions müssen für WSL neu installiert werden

#### 5.4 Empfohlene Extensions installieren (in WSL)
```bash
# Im Terminal in WSL:
code --install-extension ms-vscode.cpptools
code --install-extension ms-vscode.cmake-tools
code --install-extension ms-ossdata.vscode-pgsql
code --install-extension cweijan.vscode-postgresql-client2
code --install-extension github.copilot
code --install-extension github.copilot-chat
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
```

**Oder manuell:**
1. VS Code in WSL öffnen (`code .`)
2. Extensions Panel (Strg+Shift+X)
3. Suchen und installieren:
   - **PostgreSQL Clients:**
     - `PostgreSQL` (ms-ossdata.vscode-pgsql) 
     - `Database Client JDBC` (cweijan.dbclient-jdbc)
     - `PostgreSQL Client` (cweijan.vscode-postgresql-client2)
   - **AI-Assistenten:**
     - `GitHub Copilot` (github.copilot)
     - `GitHub Copilot Chat` (github.copilot-chat)
     - `Claude Code` (anthropic.claude-code) - optional
   - **Python:**
     - `Python` (ms-python.python)
     - `Pylance` (ms-python.vscode-pylance)

#### 5.5 VS Code Workspace einrichten
```bash
# Workspace-Datei öffnen
code POC.code-workspace
```

Falls Workspace neu erstellt werden muss:
```json
{
    "folders": [
        {
            "path": "."
        }
    ],
    "settings": {
        "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
        "python.terminal.activateEnvironment": true,
        "files.exclude": {
            "**/__pycache__": true,
            "**/*.pyc": true
        }
    }
}
```

</details>

### Phase 6: Projekt einrichten
<details>
<summary>🚀 MPC-Projekt Setup</summary>

#### 6.1 Projekt-Verzeichnis vorbereiten
```bash
# OneDrive-Pfad (automatisch synchronisiert)
cd /mnt/c/Users/[USERNAME]/OneDrive\ -\ Dr.\ Ing.\ h.c.\ F.\ Porsche\ AG/Notebooks/Projects/AI/Arch_review/POC/MPC

# ODER aus Backup entpacken
cd ~
tar -xzf MPC_project_backup_*.tar.gz
cd MPC
```

#### 6.2 Python Virtual Environment
```bash
# Virtual Environment erstellen
python3 -m venv .venv

# Aktivieren
source .venv/bin/activate

# pip aktualisieren
pip install --upgrade pip

# Requirements installieren
pip install -r requirements.txt
```

**Mögliche Fehler beheben:**
```bash
# Falls psycopg2 Fehler:
sudo apt install -y libpq-dev python3-dev

# Falls PyMuPDF Fehler:
sudo apt install -y tesseract-ocr tesseract-ocr-deu

# Dann erneut:
pip install -r requirements.txt
```

#### 6.3 Docker-Container starten
```bash
# Datenbank starten
docker compose up -d db

# Logs prüfen
docker compose logs db

# Container-Status
docker ps
```

#### 6.4 Datenbank initialisieren
```bash
# Schema erstellen
docker exec -i mpc-db-1 psql -U postgres -d mpc_db < sql/create_knowledgebase.sql

# ODER aus Backup wiederherstellen
cat backup_mpc_db_*.sql | docker exec -i mpc-db-1 psql -U postgres -d mpc_db
```

#### 6.5 Test durchführen
```bash
# Python-Umgebung aktiviert?
source .venv/bin/activate

# Datenbank anzeigen
python src/view_db.py

# Import testen
python src/import_to_db_hierarchical.py
```

</details>

---

## 📁 Zu sichernde VS Code Konfigurationen

### 1. Workspace-Dateien
```
✅ POC.code-workspace              # Multi-Folder Workspace
✅ .vscode/settings.json          # Projekt-spezifische Einstellungen (falls vorhanden)
✅ .vscode/launch.json            # Debug-Konfigurationen (falls vorhanden)
✅ .vscode/tasks.json             # Tasks (falls vorhanden)
```

### 2. Benutzer-Einstellungen (NICHT im Projekt)
Diese sind benutzerspezifisch und müssen separat notiert werden:

**Windows:**
```
%APPDATA%\Code\User\settings.json
%APPDATA%\Code\User\keybindings.json
```

**WSL (VS Code Server):**
```
~/.vscode-server/data/User/settings.json
```

### 3. Extensions-Liste exportieren
```bash
# Alle installierten Extensions auflisten
code --list-extensions > vscode_extensions.txt
```

Dann auf neuem Rechner:
```bash
# Alle Extensions installieren
cat vscode_extensions.txt | xargs -L 1 code --install-extension
```

---

## 🔒 Sicherheits-Checkliste

### Netzwerk & Firewall
- [ ] **Porsche CA-Zertifikat** installiert und aktiviert
- [ ] Windows Firewall erlaubt WSL-Netzwerk
- [ ] Docker-Container können Internet erreichen (für pip, apt)
- [ ] Proxy-Einstellungen konfiguriert (falls erforderlich)

### Proxy-Konfiguration (falls erforderlich)
```bash
# In ~/.bashrc oder /etc/environment
export HTTP_PROXY="http://proxy.porsche.de:8080"
export HTTPS_PROXY="http://proxy.porsche.de:8080"
export NO_PROXY="localhost,127.0.0.1,.porsche.de"

# Für apt
sudo nano /etc/apt/apt.conf.d/95proxies
# Acquire::http::proxy "http://proxy.porsche.de:8080/";
# Acquire::https::proxy "http://proxy.porsche.de:8080/";

# Für Docker
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo nano /etc/systemd/system/docker.service.d/http-proxy.conf
# [Service]
# Environment="HTTP_PROXY=http://proxy.porsche.de:8080"
# Environment="HTTPS_PROXY=http://proxy.porsche.de:8080"
# Environment="NO_PROXY=localhost,127.0.0.1"
```

### Berechtigungen
- [ ] Benutzer in `docker` Gruppe
- [ ] `.venv` Verzeichnis Besitzer korrekt
- [ ] Scripts haben Execute-Rechte (`chmod +x scripts/*.sh`)

---

## ⚡ Quick Setup Script

Erstellen Sie ein automatisches Setup-Script:

```bash
#!/bin/bash
# setup_wsl_complete.sh

echo "🚀 MPC Project WSL Setup"

# System aktualisieren
echo "📦 System aktualisieren..."
sudo apt update && sudo apt upgrade -y

# Essential tools
echo "🔧 Tools installieren..."
sudo apt install -y git python3 python3-pip python3-venv curl wget vim nano tree

# PDF-Tools
sudo apt install -y tesseract-ocr tesseract-ocr-deu

# Python-Dev
sudo apt install -y python3-dev build-essential libpq-dev

# CA-Zertifikat
if [ -f "PAG-Interception-CA-ROOT-01.crt" ]; then
    echo "🔐 CA-Zertifikat installieren..."
    sudo cp PAG-Interception-CA-ROOT-01.crt /usr/local/share/ca-certificates/
    sudo chmod 644 /usr/local/share/ca-certificates/PAG-Interception-CA-ROOT-01.crt
    sudo update-ca-certificates
fi

# Virtual Environment
echo "🐍 Python Virtual Environment erstellen..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Docker prüfen
if command -v docker &> /dev/null; then
    echo "✅ Docker gefunden"
    docker compose up -d db
else
    echo "⚠️  Docker nicht installiert - bitte manuell installieren"
fi

echo "✅ Setup abgeschlossen!"
echo "📝 Nächste Schritte:"
echo "   1. source .venv/bin/activate"
echo "   2. docker compose up -d"
echo "   3. python src/view_db.py"
```

---

## 🐛 Troubleshooting

### Docker startet nicht
```bash
# Service neu starten
sudo systemctl restart docker

# Logs prüfen
sudo journalctl -u docker -f

# Docker neu installieren (nur wenn nötig)
sudo apt remove docker-ce docker-ce-cli containerd.io
# dann neu installieren (siehe oben)
```

### WSL Performance-Probleme
```bash
# .wslconfig in Windows erstellen
# C:\Users\[USERNAME]\.wslconfig
[wsl2]
memory=8GB
processors=4
swap=2GB
```

### CA-Zertifikat Probleme
```bash
# Zertifikat manuell prüfen
openssl x509 -in PAG-Interception-CA-ROOT-01.crt -text -noout

# Neu installieren
sudo update-ca-certificates --fresh

# Python testen
python -c "import ssl; print(ssl.get_default_verify_paths())"
```

### VS Code Remote Connection Fehler
```bash
# VS Code Server löschen und neu installieren
rm -rf ~/.vscode-server

# Dann VS Code neu starten und erneut verbinden
```

---

## 📊 Verifikation Checklist

Nach dem Setup prüfen:

```bash
# System
✅ wsl --status                    # WSL2 läuft
✅ cat /etc/wsl.conf              # Konfiguration vorhanden

# Software
✅ python3 --version              # Python 3.12.x
✅ docker --version               # Docker 28.x
✅ docker compose version         # v2.40.x
✅ git --version                  # Git installiert

# Zertifikat
✅ ls -la /usr/local/share/ca-certificates/PAG*.crt

# Docker
✅ docker ps                      # Container laufen
✅ docker exec mpc-db-1 pg_isready  # DB erreichbar

# Python
✅ source .venv/bin/activate
✅ pip list                       # Alle Pakete installiert
✅ python src/view_db.py         # Skript läuft

# VS Code
✅ code --version                 # VS Code funktioniert
✅ code --list-extensions         # Extensions installiert
```

---

## 📞 Support & Ressourcen

### Offizielle Dokumentation
- **WSL:** https://docs.microsoft.com/windows/wsl/
- **Docker in WSL:** https://docs.docker.com/desktop/wsl/
- **VS Code Remote:** https://code.visualstudio.com/docs/remote/wsl

### Porsche-spezifisch
- IT-Helpdesk für Zertifikat-Probleme
- Netzwerk-Team für Proxy-Konfiguration

---

**Erstellt:** 9. Februar 2026  
**Letzte Aktualisierung:** 9. Februar 2026  
**Version:** 1.0
