# 🚀 Migrations-Anleitung: Transfer auf neuen Rechner

**Projekt:** MPC - PDF to Knowledge Base System  
**Datum:** 9. Februar 2026  
**Aktueller Rechner:** IT223434  

---

## 📦 Übersicht der zu übertragenden Komponenten

### 1. **Projekt-Verzeichnis** (~20 MB)
```
/mnt/c/Users/p355208/OneDrive - Dr. Ing. h.c. F. Porsche AG/Notebooks/Projects/AI/Arch_review/POC/MPC
```

### 2. **Datenbestand**

#### PDF-Dateien (4 Dateien, ~17 MB):
- `data/pdfs/050_088_LAH.893.909_Konzern Grundanforderungen Software_DE_EN_V4.6.pdf` (619 KB)
- `data/pdfs/050_091_LAH.893.910.A_Standardsoftware_DE_EN_V5.9.pdf` (358 KB)
- `data/pdfs/Leitfaden Software Architektur Dokumentation (English) _ VR5.1.0.pdf` (15 MB)
- `data/pdfs/Leitfaden Software Architektur Dokumentation (English) _ VR6.0.2.pdf` (940 KB)

#### Verarbeitete Daten (25 Dateien):
- `data/txts/` - Extrahierte Texte und JSONL-Dateien
- `data/txts_new/` - Neue Textversionen
- `data/txts_single/` - Einzelne Texte
- `data/txts_test/` - Test-Dateien
- `data/results/` - Excel-Analysedatei (81 KB)

---

## ✅ Migrations-Checkliste

### Phase 1: Vorbereitung auf aktuellem Rechner

- [ ] **1.1 Datenbank-Backup erstellen** (falls DB aktiv)
  ```bash
  # Im MPC-Verzeichnis:
  docker-compose up -d db
  docker exec -t mpc-db-1 pg_dump -U postgres mpc_db > backup_mpc_db_$(date +%Y%m%d).sql
  ```

- [ ] **1.2 Docker-Volumes prüfen**
  ```bash
  docker volume ls | grep mpc
  # Falls Volumes existieren:
  docker run --rm -v mpc_pgdata:/data -v $(pwd):/backup ubuntu tar czf /backup/pgdata_backup.tar.gz /data
  ```

- [ ] **1.3 Projekt archivieren**
  ```bash
  cd /mnt/c/Users/p355208/OneDrive\ -\ Dr.\ Ing.\ h.c.\ F.\ Porsche\ AG/Notebooks/Projects/AI/Arch_review/POC/
  tar -czf MPC_backup_$(date +%Y%m%d).tar.gz MPC/ --exclude=MPC/.venv --exclude=MPC/__pycache__
  ```

- [ ] **1.4 API-Keys sichern**
  - [ ] OpenAI API Key notieren (falls vorhanden in `.env` oder `docker-compose.yml`)
  - [ ] Andere Credentials dokumentieren

- [ ] **1.5 Aktuelle Umgebung dokumentieren**
  ```bash
  python --version > environment_info.txt
  docker --version >> environment_info.txt
  docker-compose --version >> environment_info.txt
  ```

### Phase 2: Transfer

- [ ] **2.1 Dateien kopieren**
  - **Option A:** OneDrive-Synchronisierung (empfohlen, da Projekt bereits in OneDrive)
  - **Option B:** USB-Stick/externe Festplatte
  - **Option C:** Netzwerk-Transfer (scp/rsync)

- [ ] **2.2 Zu kopierende Dateien:**
  - [ ] `MPC_backup_YYYYMMDD.tar.gz` (Haupt-Backup)
  - [ ] `backup_mpc_db_YYYYMMDD.sql` (DB-Backup, falls erstellt)
  - [ ] `pgdata_backup.tar.gz` (Volume-Backup, falls erstellt)
  - [ ] `environment_info.txt`

### Phase 3: Setup auf neuem Rechner

- [ ] **3.1 System-Voraussetzungen installieren**
  ```bash
  # Python 3.8+
  python3 --version
  
  # Docker & Docker Compose
  docker --version
  docker-compose --version
  
  # Git (optional)
  git --version
  ```

- [ ] **3.2 Projekt entpacken**
  ```bash
  # An gewünschtem Ort:
  tar -xzf MPC_backup_YYYYMMDD.tar.gz
  cd MPC/
  ```

- [ ] **3.3 Python Virtual Environment erstellen**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate  # Linux/Mac
  # oder
  .venv\Scripts\activate  # Windows
  
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

- [ ] **3.4 Docker-Container starten**
  ```bash
  docker-compose up -d db
  ```

- [ ] **3.5 Datenbank wiederherstellen** (falls Backup vorhanden)
  ```bash
  # SQL-Dump importieren:
  cat backup_mpc_db_YYYYMMDD.sql | docker exec -i mpc-db-1 psql -U postgres -d mpc_db
  
  # ODER neu initialisieren:
  docker exec -i mpc-db-1 psql -U postgres -d mpc_db < sql/create_knowledgebase.sql
  ```

- [ ] **3.6 Konfiguration anpassen**
  ```bash
  # docker-compose.yml editieren:
  # - OpenAI API Key eintragen
  # - Pfade anpassen (falls nötig)
  ```

- [ ] **3.7 Test durchführen**
  ```bash
  # Datenbankverbindung testen:
  python src/view_db.py
  
  # Import testen (falls nötig):
  python src/import_to_db_hierarchical.py
  ```

### Phase 4: Verifikation

- [ ] **4.1 Alle Dateien vorhanden?**
  ```bash
  ls -la data/pdfs/
  ls -la data/txts/
  ls -la src/
  ls -la sql/
  ```

- [ ] **4.2 Docker-Container läuft?**
  ```bash
  docker ps
  # Sollte zeigen: mpc-db-1 (ankane/pgvector)
  ```

- [ ] **4.3 Datenbank erreichbar?**
  ```bash
  docker exec -it mpc-db-1 psql -U postgres -d mpc_db -c "\dt"
  # Sollte Tabellen zeigen: chunks, chunk_categories
  ```

- [ ] **4.4 Python-Umgebung funktioniert?**
  ```bash
  source .venv/bin/activate
  python -c "import langchain; import psycopg2; import pgvector; print('All imports OK')"
  ```

---

## 📝 Wichtige Hinweise

### Dokumentation
Weitere detaillierte Anleitungen:
- **[WSL_VSCODE_SETUP.md](WSL_VSCODE_SETUP.md)** - Vollständige WSL & VS Code Konfiguration
- **[QUICK_MIGRATION.md](QUICK_MIGRATION.md)** - Quick Reference für schnelle Migration
- **[README.md](README.md)** - Projekt-Übersicht

### OneDrive-Synchronisierung
Da das Projekt bereits in OneDrive liegt, **sollte automatisch synchronisiert** werden:
- Prüfen Sie auf dem neuen Rechner die OneDrive-Synchronisierung
- Pfad wird wahrscheinlich ähnlich sein: `C:\Users\[USERNAME]\OneDrive - Dr. Ing. h.c. F. Porsche AG\Notebooks\Projects\AI\Arch_review\POC\MPC`

### Zu IGNORIERENDE Verzeichnisse (werden neu erstellt)
- `.venv/` - Python Virtual Environment (neu erstellen)
- `__pycache__/` - Python Cache
- `node_modules/` - Falls vorhanden

### Sensitive Daten
⚠️ **NICHT** ins Backup aufnehmen:
- `.env` Dateien mit API-Keys (separat übertragen)
- Passwörter
- Firmen-interne Credentials

### Docker-Volumes
- Docker-Volumes werden **nicht automatisch** übertragen
- Entweder SQL-Backup verwenden ODER Datenbank neu aufbauen

---

## 🔧 Nützliche Befehle für neuen Rechner

```bash
# Projekt-Verzeichnis aufräumen
find . -type d -name "__pycache__" -exec rm -rf {} +

# Docker komplett neu starten
docker-compose down -v
docker-compose up -d

# Datenbank komplett neu erstellen
docker exec -i mpc-db-1 psql -U postgres -d mpc_db < sql/create_knowledgebase.sql

# PDFs neu importieren
python src/pdf2text.py
python src/import_to_db_hierarchical.py

# Datenbank anzeigen
python src/view_db.py
```

---

## 📞 Troubleshooting

### Problem: Docker läuft nicht
**Lösung:** Docker Desktop installieren und starten

### Problem: Datenbank nicht erreichbar
**Lösung:** 
```bash
docker-compose logs db
docker-compose restart db
```

### Problem: Python-Pakete fehlen
**Lösung:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Problem: Permission-Fehler
**Lösung:**
```bash
chmod +x scripts/*.sh
```

---

## ✅ Erfolg überprüfen

Wenn alles funktioniert, sollten Sie:
1. ✅ Alle 4 PDF-Dateien sehen: `ls data/pdfs/`
2. ✅ Docker-Container läuft: `docker ps`
3. ✅ Datenbank erreichbar: `docker exec mpc-db-1 psql -U postgres -l`
4. ✅ Python-Skripte laufen: `python src/view_db.py`

---

**Viel Erfolg mit der Migration! 🚀**
