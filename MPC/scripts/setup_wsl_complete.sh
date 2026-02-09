#!/bin/bash

# ============================================================================
# Automatisches WSL Setup-Skript für MPC-Projekt
# ============================================================================

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Start
print_header "🚀 MPC Project - WSL Setup"

# System aktualisieren
print_header "1. System aktualisieren"
sudo apt update
sudo apt upgrade -y
print_success "System aktualisiert"

# Essential Tools
print_header "2. Essential Tools installieren"
sudo apt install -y \
    git \
    curl \
    wget \
    vim \
    nano \
    tree \
    htop \
    zip \
    unzip \
    tar \
    gzip
print_success "Tools installiert"

# Python & Development
print_header "3. Python Development Setup"
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libpq-dev
print_success "Python installiert: $(python3 --version)"

# PDF Processing Tools
print_header "4. PDF Processing Tools"
sudo apt install -y \
    tesseract-ocr \
    tesseract-ocr-deu
print_success "Tesseract OCR installiert"

# PostgreSQL Client
print_header "5. PostgreSQL Client"
if ! command -v psql &> /dev/null; then
    sudo apt install -y postgresql-client
    print_success "PostgreSQL Client installiert: $(psql --version)"
else
    print_success "PostgreSQL Client bereits vorhanden: $(psql --version)"
fi

# CA-Zertifikat
print_header "6. Porsche CA-Zertifikat installieren"
if [ -f "PAG-Interception-CA-ROOT-01.crt" ]; then
    sudo cp PAG-Interception-CA-ROOT-01.crt /usr/local/share/ca-certificates/
    sudo chmod 644 /usr/local/share/ca-certificates/PAG-Interception-CA-ROOT-01.crt
    sudo update-ca-certificates
    print_success "CA-Zertifikat installiert"
else
    print_warning "CA-Zertifikat nicht gefunden (PAG-Interception-CA-ROOT-01.crt)"
    echo "Falls erforderlich, später manuell installieren"
fi

# Docker prüfen
print_header "7. Docker prüfen"
if command -v docker &> /dev/null; then
    print_success "Docker installiert: $(docker --version)"
    print_success "Docker Compose: $(docker compose version)"
    
    # Docker-Gruppe
    if groups $USER | grep -q docker; then
        print_success "Benutzer ist in docker-Gruppe"
    else
        print_warning "Benutzer nicht in docker-Gruppe"
        echo "Führe aus: sudo usermod -aG docker $USER"
        echo "Dann: WSL neu starten (wsl --shutdown)"
    fi
else
    print_error "Docker nicht installiert!"
    echo "Bitte Docker manuell installieren (siehe WSL_VSCODE_SETUP.md)"
fi

# Git konfigurieren
print_header "8. Git konfigurieren"
if [ -z "$(git config --global user.name)" ]; then
    echo "Bitte Git-Benutzername eingeben:"
    read git_name
    git config --global user.name "$git_name"
fi

if [ -z "$(git config --global user.email)" ]; then
    echo "Bitte Git-Email eingeben:"
    read git_email
    git config --global user.email "$git_email"
fi
print_success "Git konfiguriert: $(git config --global user.name) <$(git config --global user.email)>"

# Python Virtual Environment
print_header "9. Python Virtual Environment erstellen"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    print_success "Virtual Environment erstellt"
else
    print_warning "Virtual Environment existiert bereits"
fi

source .venv/bin/activate
pip install --upgrade pip
print_success "pip aktualisiert: $(pip --version)"

# Requirements installieren
print_header "10. Python-Pakete installieren"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Requirements installiert"
    echo ""
    echo "Installierte Pakete:"
    pip list | grep -E "langchain|psycopg2|pgvector|PyMuPDF|pdfplumber" || true
else
    print_warning "requirements.txt nicht gefunden"
fi

# Docker-Container starten
print_header "11. Docker-Container starten"
if command -v docker &> /dev/null && [ -f "docker-compose.yml" ]; then
    docker compose up -d db
    sleep 5
    
    if docker ps | grep -q "pgvector\|postgres"; then
        print_success "PostgreSQL Container läuft"
        
        # Datenbank initialisieren
        if [ -f "sql/create_knowledgebase.sql" ]; then
            echo "Datenbank-Schema erstellen? (y/n)"
            read -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker exec -i mpc-db-1 psql -U postgres -d mpc_db < sql/create_knowledgebase.sql
                print_success "Datenbank-Schema erstellt"
            fi
        fi
    else
        print_warning "PostgreSQL Container konnte nicht gestartet werden"
    fi
else
    print_warning "Docker oder docker-compose.yml nicht verfügbar"
fi

# Fertig
print_header "✅ Setup abgeschlossen!"
echo ""
echo "📝 Nächste Schritte:"
echo "   1. Virtual Environment aktivieren:"
echo "      source .venv/bin/activate"
echo ""
echo "   2. Projekt testen:"
echo "      python src/view_db.py"
echo ""
echo "   3. VS Code öffnen:"
echo "      code ."
echo ""
echo "📄 Weitere Infos: siehe WSL_VSCODE_SETUP.md"
echo ""

# Zusammenfassung
print_header "📊 Installation Summary"
echo "Python:    $(python3 --version)"
echo "pip:       $(pip --version | cut -d' ' -f1-2)"
echo "Docker:    $(docker --version 2>/dev/null || echo 'Nicht installiert')"
echo "Git:       $(git --version)"
echo "PostgreSQL: $(psql --version 2>/dev/null || echo 'Nicht installiert')"
echo ""
echo "Virtual Env: $([ -d .venv ] && echo '✓ Installiert' || echo '✗ Fehlt')"
echo "CA-Cert:     $([ -f /usr/local/share/ca-certificates/PAG-Interception-CA-ROOT-01.crt ] && echo '✓ Installiert' || echo '✗ Fehlt')"
echo ""

print_success "Setup erfolgreich! 🎉"
