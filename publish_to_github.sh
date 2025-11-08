#!/bin/bash
# Schnell-Script zum Veröffentlichen auf GitHub

echo "╔═══════════════════════════════════════╗"
echo "║  KI-System → GitHub Publisher        ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# GitHub Username abfragen
read -p "Dein GitHub Username: " GITHUB_USER

if [ -z "$GITHUB_USER" ]; then
    echo -e "${RED}Fehler: GitHub Username erforderlich${NC}"
    exit 1
fi

# Repository Name
read -p "Repository Name [KI-SYSTEM]: " REPO_NAME
REPO_NAME=${REPO_NAME:-KI-SYSTEM}

# Public oder Private
read -p "Repository Public? (y/n) [y]: " IS_PUBLIC
IS_PUBLIC=${IS_PUBLIC:-y}

echo ""
echo -e "${YELLOW}Konfiguration:${NC}"
echo "  GitHub User: $GITHUB_USER"
echo "  Repo Name: $REPO_NAME"
echo "  Visibility: $([ "$IS_PUBLIC" = "y" ] && echo "Public" || echo "Private")"
echo ""
read -p "Fortfahren? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Abgebrochen."
    exit 0
fi

# 1. Git initialisieren
echo -e "${YELLOW}[1/6]${NC} Git initialisieren..."
if [ ! -d ".git" ]; then
    git init
    echo -e "${GREEN}✓${NC} Git initialisiert"
else
    echo -e "${GREEN}✓${NC} Git bereits initialisiert"
fi

# 2. Dateien hinzufügen
echo -e "${YELLOW}[2/6]${NC} Dateien zum Staging hinzufügen..."
git add .
echo -e "${GREEN}✓${NC} Dateien hinzugefügt"

# 3. Initial Commit
echo -e "${YELLOW}[3/6]${NC} Initial Commit erstellen..."
if ! git rev-parse HEAD > /dev/null 2>&1; then
    git commit -m "Initial commit: KI-System v1.1.0

Features:
- Multi-Platform Support (Home Assistant & Homey Pro)
- Machine Learning für Beleuchtung und Heizung
- Energieoptimierung
- SQLite Datenbank
- CI/CD mit GitHub Actions
- Umfangreiche Dokumentation"
    echo -e "${GREEN}✓${NC} Commit erstellt"
else
    echo -e "${GREEN}✓${NC} Commit bereits vorhanden"
fi

# 4. Branch zu main umbenennen
echo -e "${YELLOW}[4/6]${NC} Branch auf 'main' setzen..."
git branch -M main
echo -e "${GREEN}✓${NC} Branch: main"

# 5. GitHub Repository erstellen
echo -e "${YELLOW}[5/6]${NC} GitHub Repository erstellen..."

# Prüfe ob gh CLI installiert ist
if command -v gh &> /dev/null; then
    # Mit GitHub CLI
    if [ "$IS_PUBLIC" = "y" ]; then
        gh repo create "$REPO_NAME" --public --source=. --description="Intelligentes ML-basiertes Smart Home System für Home Assistant & Homey Pro" --push
    else
        gh repo create "$REPO_NAME" --private --source=. --description="Intelligentes ML-basiertes Smart Home System für Home Assistant & Homey Pro" --push
    fi
    echo -e "${GREEN}✓${NC} Repository erstellt und gepusht"
else
    # Manuell ohne gh CLI
    echo ""
    echo -e "${YELLOW}GitHub CLI nicht installiert. Manuelle Schritte:${NC}"
    echo ""
    echo "1. Gehe zu: https://github.com/new"
    echo "2. Repository Name: $REPO_NAME"
    echo "3. Visibility: $([ "$IS_PUBLIC" = "y" ] && echo "Public" || echo "Private")"
    echo "4. NICHT 'Initialize with README' ankreuzen"
    echo "5. Klicke 'Create repository'"
    echo ""
    read -p "Drücke Enter wenn Repository erstellt wurde..." 

    # 6. Remote hinzufügen und pushen
    echo -e "${YELLOW}[6/6]${NC} Mit GitHub verbinden und pushen..."
    git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
    git push -u origin main
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✓ Erfolgreich auf GitHub!          ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""
echo "Repository URL:"
echo -e "${GREEN}https://github.com/$GITHUB_USER/$REPO_NAME${NC}"
echo ""
echo "Nächste Schritte:"
echo "  1. Besuche dein Repository auf GitHub"
echo "  2. Aktiviere Issues und Discussions (Settings)"
echo "  3. Prüfe dass GitHub Actions läuft (Actions Tab)"
echo "  4. Erstelle erste Release (siehe GITHUB_SETUP.md)"
echo ""

