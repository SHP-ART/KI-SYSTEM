#!/bin/bash
# Quick fix für heating_observations Tabelle
# Führt Migration 002 manuell aus

echo "🔧 Fixing heating_observations table schema..."

# Check ob Tabelle existiert
if sqlite3 data/ki_system.db "SELECT name FROM sqlite_master WHERE type='table' AND name='heating_observations';" | grep -q "heating_observations"; then
    echo "✓ Tabelle heating_observations existiert"

    # Check ob current_temp Spalte existiert
    if sqlite3 data/ki_system.db "PRAGMA table_info(heating_observations);" | grep -q "current_temp"; then
        echo "✓ Spalte current_temp existiert bereits"
        echo "✅ Alles OK! Kein Fix nötig."
    else
        echo "❌ Spalte current_temp fehlt - Tabelle hat altes Schema"
        echo "🔄 Erstelle Tabelle neu..."

        # Backup
        cp data/ki_system.db data/ki_system.db.backup_heating
        echo "✓ Backup erstellt: data/ki_system.db.backup_heating"

        # Drop und neu erstellen
        sqlite3 data/ki_system.db < src/utils/migrations/002_add_heating_observations.sql
        echo "✅ Tabelle neu erstellt mit korrektem Schema"
    fi
else
    echo "ℹ️  Tabelle existiert noch nicht - erstelle..."
    sqlite3 data/ki_system.db < src/utils/migrations/002_add_heating_observations.sql
    echo "✅ Tabelle erstellt"
fi

echo ""
echo "📊 Aktuelles Schema:"
sqlite3 data/ki_system.db "PRAGMA table_info(heating_observations);"
echo ""
echo "✅ Fertig!"
