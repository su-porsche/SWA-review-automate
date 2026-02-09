# 📋 Checkliste: Zu sichernde Konfigurationsdateien

**Für Migration des MPC-Projekts auf neuen Rechner**

---

## ✅ Projekt-Dateien (im Projekt-Verzeichnis)

### Haupt-Konfigurationen
- [x] **docker-compose.yml** - Docker-Container-Konfiguration
- [x] **Dockerfile** - Container-Build-Anweisungen
- [x] **requirements.txt** - Python-Abhängigkeiten
- [x] **POC.code-workspace** - VS Code Multi-Folder Workspace
- [x] **.gitignore** - Git-Ignore-Regeln
- [x] **ignore_sections.json** - Projekt-spezifische Ignorierungen

### Porsche-spezifisch
- [x] **PAG-Interception-CA-ROOT-01.crt** - Corporate CA-Zertifikat (⚠️ **WICHTIG!**)
  - Muss nach Migration in WSL unter `/usr/local/share/ca-certificates/` installiert werden

### Dokumentation
- [x] **README.md** - Projekt-Übersicht
- [x] **STRUCTURE.md** - Projektstruktur
- [x] **MIGRATION_GUIDE.md** - 📘 Vollständige Migrations-Anleitung
- [x] **WSL_VSCODE_SETUP.md** - 📘 WSL & VS Code Setup
- [x] **QUICK_MIGRATION.md** - 📘 Quick Reference
- [x] Alle Dateien in `docs/` Verzeichnis

### Scripts
- [x] Alle `.sh` Dateien in `scripts/`
  - `backup_for_migration.sh` - Backup-Script
  - `setup_wsl_complete.sh` - Automatisches WSL Setup
  - `setup_db.sh`, `setup_and_import.sh`, etc.

### Daten
- [x] **data/pdfs/** - Original PDF-Dateien (4 Dateien, ~17 MB)
- [x] **data/txts/** - Verarbeitete Texte und JSONL-Dateien
- [x] **data/results/** - Analyse-Ergebnisse

### Source Code
- [x] Alle Dateien in `src/`
- [x] Alle Dateien in `tests/`
- [x] Alle Dateien in `examples/`
- [x] Alle Dateien in `sql/`

---

## 🔧 VS Code Konfigurationen

### Im Projekt (wird automatisch gesichert)
- [x] **POC.code-workspace** - Workspace-Konfiguration
- [ ] **.vscode/settings.json** - Projekt-Settings (falls vorhanden)
- [ ] **.vscode/launch.json** - Debug-Konfiguration (falls vorhanden)
- [ ] **.vscode/tasks.json** - Task-Definitionen (falls vorhanden)

### VS Code Extensions (WSL)
- [x] **vscode_extensions_wsl.txt** - Liste aller installierten Extensions
  - ✅ Wird automatisch von `backup_for_migration.sh` erstellt

**Installierte Extensions:**
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

### Benutzer-Einstellungen (⚠️ separat sichern)
Diese sind **NICHT** im Projekt und müssen separat gesichert werden:

**Windows:**
```
%APPDATA%\Code\User\settings.json
%APPDATA%\Code\User\keybindings.json
```

**WSL:**
```
~/.vscode-server/data/User/settings.json
```

**Empfehlung:** 
- Notieren Sie wesentliche Einstellungen
- Bei Standard-Einstellungen → keine Sicherung nötig

---

## 🐧 WSL-Konfigurationen

### System-Konfiguration
- [x] **/etc/wsl.conf** - WSL-Konfiguration
  - ✅ Wird automatisch von `backup_for_migration.sh` gesichert

**Inhalt (aktuell):**
```ini
[network]
generateResolvConf=true
generateHosts=true

[boot]
systemd=true

[automount]
enabled=true
```

### Bash-Konfiguration (optional)
- [ ] **~/.bashrc** - Bash-Konfiguration
- [ ] **~/.bash_profile** - Bash-Profil
- [ ] **~/.profile** - Shell-Profil

**Status:** Keine benutzerdefinierten Änderungen gefunden → keine Sicherung nötig

### Git-Konfiguration (optional)
- [ ] **~/.gitconfig** - Git-Konfiguration

**Status:** Nicht konfiguriert → muss auf neuem Rechner neu eingerichtet werden

---

## 🐳 Docker-Konfigurationen

### Container-Konfiguration
- [x] **docker-compose.yml** - Bereits im Projekt

### Docker Volumes (Datenbank-Daten)
- [ ] **PostgreSQL Volume** - Docker Volume `mpc_pgdata`

**Status:** Keine Volumes gefunden → Datenbank ist leer oder läuft nicht

**Migration-Strategie:**
- Falls Daten vorhanden: SQL-Dump erstellen (wird von `backup_for_migration.sh` gemacht)
- Auf neuem Rechner: Datenbank neu initialisieren aus SQL-Dump

---

## 🔐 Sicherheits-/Netzwerk-Konfigurationen

### CA-Zertifikat
- [x] **PAG-Interception-CA-ROOT-01.crt** (im Projekt)
- [x] Installation unter `/usr/local/share/ca-certificates/`

**Auf neuem Rechner:**
```bash
sudo cp PAG-Interception-CA-ROOT-01.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

### Proxy-Einstellungen (falls erforderlich)
- [ ] **HTTP_PROXY / HTTPS_PROXY** Umgebungsvariablen
- [ ] **/etc/apt/apt.conf.d/95proxies** - APT Proxy
- [ ] **/etc/systemd/system/docker.service.d/http-proxy.conf** - Docker Proxy

**Status:** Keine Proxy-Konfiguration gefunden → nicht erforderlich oder automatisch konfiguriert

### API-Keys & Credentials
- [ ] **OpenAI API Key** (falls verwendet)
- [ ] **PostgreSQL Password** (Standard: `postgres` in docker-compose.yml)

**⚠️ WICHTIG:** API-Keys **NICHT** ins Backup aufnehmen!
- Separat notieren
- Auf neuem Rechner: In `docker-compose.yml` oder `.env` eintragen

---

## 📦 Was NICHT gesichert werden muss

### Automatisch generierte Dateien
- [ ] **.venv/** - Python Virtual Environment (neu erstellen)
- [ ] **__pycache__/** - Python Cache
- [ ] **node_modules/** - Falls vorhanden
- [ ] **.git/** - Falls Git verwendet (optional)

### Docker
- [ ] **Docker Images** - Werden neu heruntergeladen
- [ ] **Docker Volumes** - SQL-Dump stattdessen

### VS Code
- [ ] **~/.vscode-server/** - Wird automatisch neu installiert

---

## 🚀 Automatische Sicherung

Das Script **`scripts/backup_for_migration.sh`** sichert automatisch:

```bash
./scripts/backup_for_migration.sh
```

**Was wird gesichert:**
- ✅ Komplettes Projekt (tar.gz) ohne `.venv`, `__pycache__`
- ✅ Datenbank-Backup (SQL, falls vorhanden)
- ✅ Docker-Status und Volumes
- ✅ Umgebungs-Informationen (Python, Docker, Git Versionen)
- ✅ Projekt-Inventar (Dateizahlen, Größen)
- ✅ Alle Konfigurationsdateien
- ✅ CA-Zertifikat
- ✅ VS Code Extensions-Liste
- ✅ WSL-Konfiguration

**Backup-Verzeichnis:** `./backups/[DATUM_ZEIT]/`

---

## 📋 Manuelle Checkliste

### Vor Migration (Alter Rechner)
- [ ] Backup erstellen: `./scripts/backup_for_migration.sh`
- [ ] API-Keys separat notieren
- [ ] OneDrive-Synchronisierung prüfen
- [ ] Backup-Verzeichnis auf USB/Netzwerk kopieren (falls nicht OneDrive)

### Nach Migration (Neuer Rechner)
- [ ] WSL2 installieren
- [ ] Ubuntu 24.04 installieren
- [ ] WSL konfigurieren (`/etc/wsl.conf`)
- [ ] Docker installieren
- [ ] CA-Zertifikat installieren
- [ ] Projekt aus OneDrive/Backup kopieren
- [ ] Setup ausführen: `./scripts/setup_wsl_complete.sh`
- [ ] VS Code installieren
- [ ] VS Code Extensions installieren
- [ ] API-Keys in `docker-compose.yml` eintragen
- [ ] Testen: `python src/view_db.py`

---

## 📊 Zusammenfassung

| Kategorie | Anzahl Dateien | Automatisch gesichert |
|-----------|----------------|----------------------|
| Projekt-Code | ~50 | ✅ Ja |
| Konfigurationsdateien | 10 | ✅ Ja |
| PDFs | 4 | ✅ Ja |
| Verarbeitete Daten | 25 | ✅ Ja |
| Scripts | 4 | ✅ Ja |
| Dokumentation | 10+ | ✅ Ja |
| CA-Zertifikat | 1 | ✅ Ja |
| VS Code Extensions | 11 | ✅ Liste exportiert |
| WSL-Konfiguration | 1 | ✅ Ja |
| **Gesamt** | **116+** | **✅ Vollständig** |

---

## 📞 Weitere Informationen

- **Vollständige Anleitung:** [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- **WSL & VS Code Setup:** [WSL_VSCODE_SETUP.md](WSL_VSCODE_SETUP.md)
- **Quick Reference:** [QUICK_MIGRATION.md](QUICK_MIGRATION.md)

---

**Stand:** 9. Februar 2026  
**Version:** 1.0
