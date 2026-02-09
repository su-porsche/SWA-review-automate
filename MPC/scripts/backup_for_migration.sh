#!/bin/bash

# ============================================================================
# Backup-Skript für Migration auf neuen Rechner
# ============================================================================
# Dieses Skript erstellt ein vollständiges Backup des MPC-Projekts
# für die Übertragung auf einen neuen Rechner
# ============================================================================

set -e  # Exit bei Fehler

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Variablen
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/${BACKUP_DATE}"
PROJECT_ROOT=$(pwd)

# Start
print_header "MPC Projekt Backup für Migration"
echo "Backup-Verzeichnis: ${BACKUP_DIR}"
echo "Projekt-Verzeichnis: ${PROJECT_ROOT}"
echo ""

# Backup-Verzeichnis erstellen
mkdir -p "${BACKUP_DIR}"
print_success "Backup-Verzeichnis erstellt"

# 1. Umgebungs-Informationen sammeln
print_header "1. Umgebungs-Informationen sammeln"
{
    echo "=== System Information ==="
    echo "Date: $(date)"
    echo "Hostname: $(hostname)"
    echo "User: $(whoami)"
    echo ""
    echo "=== Software Versions ==="
    echo "Python: $(python --version 2>&1 || python3 --version 2>&1)"
    echo "Docker: $(docker --version 2>&1 || echo 'Not installed')"
    echo "Docker Compose: $(docker-compose --version 2>&1 || echo 'Not installed')"
    echo ""
    echo "=== Installed Python Packages ==="
    if [ -d ".venv" ]; then
        source .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate 2>/dev/null || true
        pip list 2>/dev/null || echo "Could not list packages"
    else
        echo "No virtual environment found"
    fi
} > "${BACKUP_DIR}/environment_info.txt"
print_success "Umgebungs-Info gespeichert: environment_info.txt"

# 2. Docker-Status prüfen
print_header "2. Docker-Container und Volumes prüfen"
{
    echo "=== Docker Containers ==="
    docker ps -a 2>&1 || echo "Docker not running"
    echo ""
    echo "=== Docker Volumes ==="
    docker volume ls 2>&1 || echo "Docker not running"
} > "${BACKUP_DIR}/docker_status.txt"
print_success "Docker-Status gespeichert: docker_status.txt"

# 3. Datenbank-Backup (falls DB läuft)
print_header "3. Datenbank-Backup erstellen"
if docker ps | grep -q "pgvector\|mpc.*db"; then
    print_warning "PostgreSQL Container gefunden - versuche Backup..."
    
    # Container-Name finden
    DB_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E 'db|postgres' | head -1)
    
    if [ -n "$DB_CONTAINER" ]; then
        echo "Verwende Container: $DB_CONTAINER"
        
        # SQL Dump erstellen
        if docker exec -t "$DB_CONTAINER" pg_dump -U postgres mpc_db > "${BACKUP_DIR}/mpc_db_backup.sql" 2>/dev/null; then
            print_success "Datenbank-Backup erstellt: mpc_db_backup.sql ($(du -h ${BACKUP_DIR}/mpc_db_backup.sql | cut -f1))"
        else
            print_warning "Konnte kein SQL-Dump erstellen (evtl. leere DB)"
        fi
        
        # Tabellen-Info
        docker exec -t "$DB_CONTAINER" psql -U postgres -d mpc_db -c "\dt" > "${BACKUP_DIR}/database_tables.txt" 2>/dev/null || true
        docker exec -t "$DB_CONTAINER" psql -U postgres -d mpc_db -c "SELECT table_name, pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS size FROM information_schema.tables WHERE table_schema = 'public';" > "${BACKUP_DIR}/database_sizes.txt" 2>/dev/null || true
    else
        print_warning "Kein PostgreSQL Container aktiv"
    fi
else
    print_warning "Keine laufende Datenbank gefunden - skip DB-Backup"
    echo "Keine laufende Datenbank gefunden" > "${BACKUP_DIR}/no_database.txt"
fi

# 4. Projekt-Dateien inventarisieren
print_header "4. Projekt-Dateien inventarisieren"
{
    echo "=== Projekt-Struktur ==="
    tree -L 3 -I '.venv|__pycache__|*.pyc' . 2>/dev/null || find . -maxdepth 3 -not -path '*/.venv/*' -not -path '*/__pycache__/*' | sort
    echo ""
    echo "=== Dateigrößen ==="
    du -sh data/pdfs/* 2>/dev/null || echo "Keine PDFs"
    echo ""
    echo "=== Anzahl Dateien ==="
    echo "PDFs: $(find data/pdfs -type f 2>/dev/null | wc -l)"
    echo "TXTs: $(find data/txts* -type f -name '*.txt' 2>/dev/null | wc -l)"
    echo "JSONLs: $(find data/txts* -type f -name '*.jsonl' 2>/dev/null | wc -l)"
    echo "Python-Dateien: $(find src tests -type f -name '*.py' 2>/dev/null | wc -l)"
} > "${BACKUP_DIR}/project_inventory.txt"
print_success "Projekt-Inventar erstellt: project_inventory.txt"

# 5. Wichtige Konfigurationsdateien kopieren
print_header "5. Konfigurationsdateien kopieren"
for file in docker-compose.yml Dockerfile requirements.txt README.md STRUCTURE.md .gitignore POC.code-workspace; do
    if [ -f "$file" ]; then
        cp "$file" "${BACKUP_DIR}/"
        print_success "Kopiert: $file"
    fi
done

# CA-Zertifikat (wichtig für Corporate Network)
if [ -f "PAG-Interception-CA-ROOT-01.crt" ]; then
    cp "PAG-Interception-CA-ROOT-01.crt" "${BACKUP_DIR}/"
    print_success "Kopiert: CA-Zertifikat"
fi

# VS Code Extensions exportieren
if command -v code &> /dev/null; then
    code --list-extensions > "${BACKUP_DIR}/vscode_extensions_wsl.txt" 2>/dev/null || true
    if [ -f "${BACKUP_DIR}/vscode_extensions_wsl.txt" ]; then
        print_success "VS Code Extensions exportiert ($(wc -l < ${BACKUP_DIR}/vscode_extensions_wsl.txt) Extensions)"
    fi
fi

# WSL-Konfiguration exportieren
if [ -f "/etc/wsl.conf" ]; then
    sudo cat /etc/wsl.conf > "${BACKUP_DIR}/wsl.conf" 2>/dev/null || true
    print_success "WSL-Konfiguration exportiert"
fi

# 6. Projekt-Archiv erstellen (ohne .venv und __pycache__)
print_header "6. Projekt-Archiv erstellen"
ARCHIVE_NAME="MPC_project_backup_${BACKUP_DATE}.tar.gz"
print_warning "Erstelle Archiv (kann einige Minuten dauern)..."

tar -czf "${BACKUP_DIR}/${ARCHIVE_NAME}" \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='backups' \
    --exclude='node_modules' \
    . 2>/dev/null

if [ -f "${BACKUP_DIR}/${ARCHIVE_NAME}" ]; then
    ARCHIVE_SIZE=$(du -h "${BACKUP_DIR}/${ARCHIVE_NAME}" | cut -f1)
    print_success "Projekt-Archiv erstellt: ${ARCHIVE_NAME} (${ARCHIVE_SIZE})"
else
    print_error "Fehler beim Erstellen des Archivs"
fi

# 7. Zusammenfassung erstellen
print_header "7. Backup-Zusammenfassung"
{
    echo "=================================================="
    echo "MPC Projekt Backup - Zusammenfassung"
    echo "=================================================="
    echo ""
    echo "Backup-Datum: ${BACKUP_DATE}"
    echo "Backup-Verzeichnis: ${BACKUP_DIR}"
    echo ""
    echo "Erstelle Dateien:"
    echo "----------------"
    ls -lh "${BACKUP_DIR}"
    echo ""
    echo "Gesamtgröße Backup:"
    du -sh "${BACKUP_DIR}"
    echo ""
    echo "=================================================="
    echo "Nächste Schritte für Migration:"
    echo "=================================================="
    echo "1. Kopiere das gesamte 'backups/${BACKUP_DATE}' Verzeichnis"
    echo "   auf den neuen Rechner"
    echo ""
    echo "2. Entpacke auf neuem Rechner:"
    echo "   tar -xzf ${ARCHIVE_NAME}"
    echo ""
    echo "3. Folge der Anleitung in MIGRATION_GUIDE.md"
    echo ""
    echo "4. Falls Datenbank-Backup vorhanden:"
    echo "   cat mpc_db_backup.sql | docker exec -i mpc-db-1 psql -U postgres -d mpc_db"
    echo ""
} | tee "${BACKUP_DIR}/BACKUP_README.txt"

print_success "Zusammenfassung erstellt: BACKUP_README.txt"

# Fertig!
print_header "✅ Backup erfolgreich erstellt!"
echo -e "${GREEN}Backup-Verzeichnis: ${BACKUP_DIR}${NC}"
echo ""
echo "📦 Zu übertragende Dateien:"
echo "   → ${BACKUP_DIR}/"
echo ""
echo "📄 Siehe auch: MIGRATION_GUIDE.md für detaillierte Migrations-Anleitung"
echo ""

# Optional: Backup-Verzeichnis öffnen
if command -v xdg-open &> /dev/null; then
    read -p "Backup-Verzeichnis jetzt öffnen? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open "${BACKUP_DIR}"
    fi
elif command -v explorer.exe &> /dev/null; then
    read -p "Backup-Verzeichnis jetzt öffnen? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        explorer.exe "$(wslpath -w "${BACKUP_DIR}")"
    fi
fi

print_success "Fertig! 🚀"
