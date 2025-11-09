# Daten-Persistenz & Updates

Dieses Dokument erklärt, welche Daten bei Updates erhalten bleiben und wie Sie Ihre Einstellungen sichern.

## 🔒 Automatisch geschützte Dateien

Die folgenden Dateien werden **NICHT** von Git getrackt und bleiben bei Updates automatisch erhalten:

### Datenbank
```
data/ki_system.db           # Hauptdatenbank mit allen Sensor-Daten, Events, Entscheidungen
data/ki_system.db-shm       # SQLite Shared Memory
data/ki_system.db-wal       # SQLite Write-Ahead Log
```

### Konfigurationsdateien
```
data/luftentfeuchten_config.json    # Badezimmer-Automatisierung Konfiguration
data/bathroom_config.json           # Alternative Badezimmer-Config
data/sensor_config.json             # Sensor-Whitelist und Metadaten
data/heating_mode.json              # Heizungs-Modus (Steuerung vs. Optimierung)
data/settings_general.json          # Allgemeine Einstellungen (Datensammlung, Entscheidungs-Engine)
data/ml_training_status.json        # ML-Trainings-Status
```

### Trainierte ML-Modelle
```
models/lighting_model.pkl           # Trainiertes Beleuchtungs-Modell
models/temperature_model.pkl        # Trainiertes Temperatur-Modell
models/energy_optimizer.pkl         # Trainierter Energie-Optimierer
```

### Credentials & Secrets
```
.env                                # API-Keys, Tokens, URLs
```

### Logs
```
logs/ki_system.log                  # Alle Log-Dateien
```

### Backups
```
data/backups/                       # Automatische Datenbank-Backups
```

## 📦 Update-Prozess

### Option 1: Update über Web-Interface (Empfohlen ⭐)

1. Öffne das Web-Dashboard: `http://localhost:5000/settings`
2. Gehe zum Tab **"System"**
3. Klicke auf **"Nach Updates suchen"**
4. Falls Updates verfügbar: Klicke auf **"Update installieren"**
5. Das System erstellt automatisch ein Backup und startet neu

**Vorteile:**
- ✅ Automatisches Backup vor dem Update
- ✅ Automatischer Neustart
- ✅ Keine Terminal-Befehle nötig
- ✅ Zeigt verfügbare Änderungen an

### Option 2: Manuelles Update via Git

Wenn Sie ein Update durchführen, bleiben **alle oben genannten Dateien automatisch erhalten**:

```bash
git pull origin main
```

✅ **Ihre Daten sind sicher!** Keine manuelle Sicherung nötig.

### Was passiert bei einem Update?

| Datei-Typ | Bei Update | Nach Update |
|-----------|------------|-------------|
| **Code** (Python, HTML, JS) | ✓ Wird aktualisiert | Neue Features verfügbar |
| **Datenbank** | ✗ Bleibt unverändert | Alle Daten erhalten |
| **Konfigurationen** | ✗ Bleiben unverändert | Alle Einstellungen erhalten |
| **ML-Modelle** | ✗ Bleiben unverändert | Trainierte Modelle erhalten |
| **.env** | ✗ Bleibt unverändert | Credentials sicher |

### 🛡️ Automatische Backups beim Web-Update

Wenn Sie über das Web-Interface updaten (`update.sh` Script):

1. **Vor dem Update** wird automatisch ein Backup erstellt:
   ```
   .backup/20250109_143022/
   ├── .env           # Ihre Credentials
   ├── data/          # Komplette Datenbank + Configs
   └── models/        # Trainierte ML-Modelle
   ```

2. **Backup-Aufbewahrung**: 7 Tage
   - Alte Backups (> 7 Tage) werden automatisch gelöscht
   - Die neuesten 7 Tage bleiben erhalten

3. **Wiederherstellung bei Problemen**:
   ```bash
   # Finde neuestes Backup
   ls -lt .backup/

   # Wiederherstellen (Beispiel vom 09.01.2025 14:30)
   cp -r .backup/20250109_143022/data/* data/
   cp -r .backup/20250109_143022/models/* models/
   cp .backup/20250109_143022/.env .env
   ```

## 🛡️ Manuelles Backup (Optional)

Für zusätzliche Sicherheit können Sie ein manuelles Backup erstellen:

### Schnell-Backup (nur Datenbank)
```bash
cp data/ki_system.db data/backups/ki_system_$(date +%Y%m%d).db
```

### Vollständiges Backup (alle Daten)
```bash
# Backup-Verzeichnis erstellen
mkdir -p backups/$(date +%Y%m%d)

# Datenbank sichern
cp data/*.db backups/$(date +%Y%m%d)/

# Konfigurationen sichern
cp data/*.json backups/$(date +%Y%m%d)/

# ML-Modelle sichern
cp models/*.pkl backups/$(date +%Y%m%d)/

# .env sichern
cp .env backups/$(date +%Y%m%d)/
```

### Backup wiederherstellen
```bash
# Beispiel: Backup vom 15. Januar 2025 wiederherstellen
cp backups/20250115/ki_system.db data/
cp backups/20250115/*.json data/
cp backups/20250115/*.pkl models/
cp backups/20250115/.env .
```

## 🔄 Migration bei Schema-Änderungen

Falls ein Update die Datenbank-Struktur ändert, wird dies automatisch erkannt:

1. **Automatische Migration**: Das System erkennt fehlende Tabellen/Spalten und erstellt sie automatisch
2. **Alte Daten bleiben erhalten**: Bestehende Daten werden nicht gelöscht
3. **Logs prüfen**: Schauen Sie in `logs/ki_system.log` nach Migrations-Meldungen

### Beispiel-Log bei Migration:
```
INFO: Database schema updated: Added column 'new_field' to table 'sensor_data'
INFO: Existing data preserved: 15234 rows
```

## 📋 Checklist nach Update

Nach einem `git pull` sollten Sie:

- [ ] Virtuelle Umgebung aktualisieren: `pip install -r requirements.txt --upgrade`
- [ ] Web-App neu starten: `python3 main.py web`
- [ ] Logs prüfen: `tail -f logs/ki_system.log`
- [ ] Einstellungen überprüfen: `http://localhost:5000/settings`
- [ ] Badezimmer-Config überprüfen (falls genutzt): `http://localhost:5000/luftentfeuchten`

## 🚨 Notfall: Daten versehentlich gelöscht?

Falls Dateien versehentlich gelöscht wurden:

### Datenbank wiederherstellen
```bash
# Von automatischem Backup (falls vorhanden)
cp data/backups/ki_system_latest.db data/ki_system.db

# Oder von manuellem Backup
cp backups/[DATUM]/ki_system.db data/
```

### Konfigurationen neu erstellen
Falls Konfigurationsdateien fehlen:

1. **Badezimmer**: Gehe zu `/luftentfeuchten` und konfiguriere neu
2. **Allgemeine Einstellungen**: Gehe zu `/settings` → Tab "Allgemein"
3. **Heizung**: Gehe zu `/heating` und wähle Modus

Die Dateien werden automatisch beim ersten Speichern neu erstellt.

## 📝 Best Practices

1. **Regelmäßige Backups**: Erstellen Sie wöchentlich manuelle Backups
2. **Vor großen Updates**: Backup erstellen vor `git pull`
3. **Nach ML-Training**: Backup der `.pkl` Modelle nach erfolgreichem Training
4. **Retention**: Alte Backups nach 90 Tagen löschen (automatisch in `data/backups/`)

## 🔍 Überprüfung der Persistenz

Sie können jederzeit prüfen, welche Dateien von Git ignoriert werden:

```bash
# Zeige ignorierte Dateien im data/ Verzeichnis
git status --ignored data/

# Zeige alle ignorierten Dateien
git status --ignored
```

Ausgabe sollte zeigen:
```
Ignored files:
  data/ki_system.db
  data/luftentfeuchten_config.json
  data/settings_general.json
  models/lighting_model.pkl
  ...
```

## 💡 Häufige Fragen

**Q: Muss ich vor jedem Update ein Backup machen?**
A: Nein! Beim Web-Update wird automatisch ein Backup erstellt. Bei manuellem `git pull` sind alle Daten durch .gitignore geschützt.

**Q: Was ist der Unterschied zwischen Web-Update und git pull?**
A:
- **Web-Update**: Erstellt automatisch Backup, aktualisiert Dependencies, startet System neu
- **git pull**: Schneller, aber ohne automatisches Backup oder Neustart (Daten trotzdem sicher durch .gitignore)

**Q: Was passiert mit meinen Einstellungen nach `git pull`?**
A: Alle Einstellungen bleiben erhalten, da sie in ignorierten JSON-Dateien im `data/` Verzeichnis gespeichert sind.

**Q: Gehen meine trainierten ML-Modelle verloren?**
A: Nein, alle `.pkl` Dateien im `models/` Verzeichnis bleiben erhalten.

**Q: Kann ich die Datenbank auf einen anderen Computer kopieren?**
A: Ja! Kopieren Sie einfach `data/ki_system.db` und alle `data/*.json` Dateien auf den neuen Computer.

**Q: Wie groß wird die Datenbank?**
A: Abhängig von der Datensammlung. Typisch: 10-100 MB. Automatische Bereinigung nach 90 Tagen (konfigurierbar unter `/settings` → Tab "Datenbank").

---

**Letzte Aktualisierung**: 2025-01-09
**Gilt für Version**: v0.8+
