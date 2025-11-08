# GitHub Setup Anleitung

So veröffentlichst du das KI-System auf GitHub.

## Schritt 1: Git Repository initialisieren

```bash
cd /Users/shp-art/Documents/Github/KI-SYSTEM

# Git initialisieren (falls noch nicht)
git init

# .gitignore prüfen
cat .gitignore

# Alle Dateien zum Staging hinzufügen
git add .

# Ersten Commit erstellen
git commit -m "Initial commit: KI-System v1.1.0

Features:
- Multi-Platform Support (Home Assistant & Homey Pro)
- Machine Learning für Beleuchtung und Heizung
- Energieoptimierung
- SQLite Datenbank
- CI/CD mit GitHub Actions
- Umfangreiche Dokumentation"
```

## Schritt 2: GitHub Repository erstellen

### Option A: Via GitHub Website

1. **Gehe zu [GitHub](https://github.com)**
2. **Klicke auf "+" → "New repository"**
3. **Repository-Einstellungen:**
   - Name: `KI-SYSTEM` (oder dein Wunschname)
   - Description: `Intelligentes ML-basiertes Smart Home Automatisierungssystem für Home Assistant & Homey Pro`
   - Visibility: `Public` (oder `Private`)
   - ❌ **NICHT** "Initialize with README" ankreuzen (haben wir schon!)
   - ❌ **NICHT** .gitignore hinzufügen (haben wir schon!)
   - ✅ License: MIT (auswählen)

4. **Klicke "Create repository"**

### Option B: Via GitHub CLI

```bash
# GitHub CLI installieren (falls noch nicht)
# Mac: brew install gh
# Linux: siehe https://cli.github.com/

# Login
gh auth login

# Repository erstellen
gh repo create KI-SYSTEM --public --source=. --description="Intelligentes ML-basiertes Smart Home System"

# Oder privat:
# gh repo create KI-SYSTEM --private --source=. --description="..."
```

## Schritt 3: Local zu GitHub pushen

Nach der Repository-Erstellung zeigt GitHub dir die Commands. Nutze diese:

```bash
# Remote hinzufügen (ersetze USERNAME mit deinem GitHub Username)
git remote add origin https://github.com/USERNAME/KI-SYSTEM.git

# Prüfe Remote
git remote -v

# Branch umbenennen zu main (falls noch master)
git branch -M main

# Push zum GitHub
git push -u origin main
```

**Ausgabe sollte sein:**
```
Enumerating objects: 150, done.
Counting objects: 100% (150/150), done.
Delta compression using up to 8 threads
Compressing objects: 100% (120/120), done.
Writing objects: 100% (150/150), 250 KiB | 5 MiB/s, done.
Total 150 (delta 25), reused 0 (delta 0)
To https://github.com/USERNAME/KI-SYSTEM.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

## Schritt 4: Repository Settings konfigurieren

### A) Branches schützen

1. Gehe zu Repository → **Settings** → **Branches**
2. Klicke **Add rule** unter "Branch protection rules"
3. Branch name pattern: `main`
4. Aktiviere:
   - ✅ **Require pull request reviews before merging**
   - ✅ **Require status checks to pass before merging**
     - Wähle: `test (3.8, 3.9, 3.10, 3.11)`
   - ✅ **Require branches to be up to date before merging**
5. Klicke **Create**

### B) Issues aktivieren

1. **Settings** → **General**
2. Features Section:
   - ✅ **Issues** aktivieren
   - ✅ **Discussions** aktivieren (optional aber empfohlen)
   - ✅ **Projects** aktivieren (optional)

### C) Topics hinzufügen

1. Hauptseite des Repositories
2. Klicke auf **⚙️** neben "About"
3. Füge Topics hinzu:
   ```
   smart-home
   home-assistant
   homey-pro
   machine-learning
   home-automation
   python
   iot
   energy-optimization
   ```

### D) Repository Description

```
🏠 Intelligentes ML-basiertes Smart Home Automatisierungssystem für Home Assistant & Homey Pro mit Energieoptimierung
```

### E) Website (optional)

Falls du GitHub Pages nutzen möchtest oder eine andere URL hast

## Schritt 5: GitHub Actions prüfen

Nach dem Push:

1. Gehe zu **Actions** Tab
2. Du solltest sehen: "CI" Workflow
3. Erster Run startet automatisch
4. Warten bis ✅ grün wird

Falls Fehler:
- Klicke auf den fehlgeschlagenen Job
- Prüfe Logs
- Fixe Fehler lokal
- Push erneut

## Schritt 6: Release erstellen (optional)

### Erste Release

```bash
# Tag erstellen
git tag -a v1.1.0 -m "Release v1.1.0

Features:
- Multi-Platform Support (Home Assistant & Homey Pro)
- ML-basierte Automatisierung
- Energieoptimierung
- Umfangreiche Dokumentation

Breaking Changes:
- Energiepreis-Integration jetzt standardmäßig deaktiviert

See CHANGELOG.md for details"

# Tag pushen
git push origin v1.1.0
```

### GitHub Release Page

1. Gehe zu **Releases** → **Create a new release**
2. Tag: `v1.1.0` (auswählen)
3. Title: `KI-System v1.1.0 - Multi-Platform Support`
4. Description:
   ```markdown
   ## 🎉 Erstes offizielles Release!

   ### ✨ Features
   - 🏠 Multi-Platform Support (Home Assistant & Homey Pro)
   - 🤖 Machine Learning für Beleuchtung und Heizung
   - ⚡ Energieoptimierung
   - 📊 SQLite Datenbank
   - 🔄 CI/CD Pipeline
   - 📚 Umfangreiche Dokumentation

   ### 📥 Installation
   Siehe [Installation Guide](README.md#installation)

   ### 📖 Dokumentation
   - [Quick Start Guide](QUICK_START.md)
   - [Testing Guide](TESTING.md)
   - [Platform Comparison](PLATFORMS.md)

   ### 🐛 Bug Fixes
   Siehe [CHANGELOG.md](CHANGELOG.md)
   ```

5. Klicke **Publish release**

## Schritt 7: README Badges aktualisieren

Die Badges im README zeigen Status:

```markdown
[![CI](https://github.com/USERNAME/KI-SYSTEM/workflows/CI/badge.svg)](https://github.com/USERNAME/KI-SYSTEM/actions)
[![Release](https://img.shields.io/github/v/release/USERNAME/KI-SYSTEM)](https://github.com/USERNAME/KI-SYSTEM/releases)
```

Ersetze `USERNAME` mit deinem GitHub Username.

## Schritt 8: Social Preview Image (optional)

1. **Settings** → **General** → **Social preview**
2. Upload ein Bild (1280x640px empfohlen)
3. Zeigt sich wenn jemand dein Repo teilt

## Normale Workflow danach

### Änderungen pushen

```bash
# Änderungen machen
nano src/some_file.py

# Staging
git add .

# Commit
git commit -m "Add new feature: XYZ"

# Push
git push origin main
```

### Feature Branch Workflow

```bash
# Neuer Branch
git checkout -b feature/neue-funktion

# Änderungen machen & committen
git add .
git commit -m "Implement neue Funktion"

# Push Branch
git push origin feature/neue-funktion

# Auf GitHub → Create Pull Request
# Nach Review & Tests → Merge
```

## Troubleshooting

### "Permission denied (publickey)"

```bash
# SSH Key generieren
ssh-keygen -t ed25519 -C "deine@email.com"

# Key zu GitHub hinzufügen
# Settings → SSH and GPG keys → New SSH Key
# Paste den Inhalt von ~/.ssh/id_ed25519.pub
```

### "failed to push some refs"

```bash
# Pull zuerst
git pull origin main --rebase

# Dann push
git push origin main
```

### Große Dateien

GitHub hat ein Limit von 100MB pro Datei.

Falls du größere Dateien hast:
```bash
# Git LFS installieren
git lfs install

# Track große Dateien
git lfs track "*.pkl"
git lfs track "*.h5"

# .gitattributes committen
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

## Best Practices

### Commit Messages

```bash
# Gut
git commit -m "Fix temperature sensor reading bug

- Handle None values in sensor data
- Add validation for temperature range
- Update tests

Fixes #42"

# Nicht gut
git commit -m "fix bug"
```

### Branching Strategy

- `main` - Stable releases
- `develop` - Development branch (optional)
- `feature/*` - Neue Features
- `fix/*` - Bug Fixes
- `docs/*` - Dokumentation

### Regelmäßige Updates

```bash
# Täglich oder wöchentlich
git pull origin main
git push origin main
```

## Nächste Schritte

Nach GitHub Setup:

1. ✅ **README.md anpassen**
   - Dein GitHub Username
   - Badges aktualisieren
   - Screenshots hinzufügen (optional)

2. ✅ **Community Files**
   - CONTRIBUTING.md ist da ✓
   - CODE_OF_CONDUCT.md ist da ✓
   - Issue Templates sind da ✓

3. ✅ **GitHub Actions**
   - CI läuft automatisch ✓
   - Bei jedem Push/PR ✓

4. ✅ **Star dein eigenes Projekt** 😄

5. ✅ **Teile es!**
   - Reddit: r/homeassistant, r/selfhosted
   - Home Assistant Community Forum
   - Homey Community Forum

## Projekt bewerben

### Wo posten?

- **Home Assistant Community**: https://community.home-assistant.io/
- **Reddit**: r/homeassistant, r/homeautomation
- **Homey Forum**: https://community.homey.app/
- **GitHub Topics**: smart-home, home-automation

### Beispiel-Post

```markdown
🤖 KI-System: ML-basierte Smart Home Automatisierung

Ich habe ein System entwickelt das mit Machine Learning lernt,
wann Licht an/aus und wie warm es sein sollte.

Features:
- Home Assistant & Homey Pro Support
- Lernt aus deinem Verhalten
- Energieoptimierung
- Open Source (MIT)

GitHub: [Link]
Feedback willkommen!
```

---

**Fertig!** 🎉 Dein Projekt ist jetzt auf GitHub!
