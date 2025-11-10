#!/usr/bin/env python3
"""
Fix-Script für heating_observations Tabelle
Führt Migration 002 manuell aus wenn nötig
"""

import sqlite3
import sys
from pathlib import Path

def main():
    db_path = Path("data/ki_system.db")
    migration_path = Path("src/utils/migrations/002_add_heating_observations.sql")

    print("🔧 Fixing heating_observations table schema...")

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        sys.exit(1)

    # Verbinde zur Datenbank
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check ob Tabelle existiert
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='heating_observations'"
        )
        table_exists = cursor.fetchone() is not None

        if table_exists:
            print("✓ Tabelle heating_observations existiert")

            # Check ob current_temp Spalte existiert
            cursor.execute("PRAGMA table_info(heating_observations)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            if 'current_temp' in column_names:
                print("✓ Spalte current_temp existiert bereits")
                print("✅ Alles OK! Kein Fix nötig.")
            else:
                print("❌ Spalte current_temp fehlt - Tabelle hat altes Schema")
                print("🔄 Erstelle Tabelle neu...")

                # Backup (einfach durch alte Daten löschen)
                cursor.execute("DROP TABLE IF EXISTS heating_observations")

                # Führe Migration aus
                with open(migration_path, 'r') as f:
                    migration_sql = f.read()

                cursor.executescript(migration_sql)
                conn.commit()
                print("✅ Tabelle neu erstellt mit korrektem Schema")
        else:
            print("ℹ️  Tabelle existiert noch nicht - erstelle...")

            # Führe Migration aus
            with open(migration_path, 'r') as f:
                migration_sql = f.read()

            cursor.executescript(migration_sql)
            conn.commit()
            print("✅ Tabelle erstellt")

        # Zeige finales Schema
        print("\n📊 Aktuelles Schema:")
        cursor.execute("PRAGMA table_info(heating_observations)")
        columns = cursor.fetchall()

        print(f"{'ID':<5} {'Name':<25} {'Type':<15} {'NotNull':<10} {'Default':<15}")
        print("-" * 75)
        for col in columns:
            col_id, name, col_type, not_null, default_val, pk = col
            print(f"{col_id:<5} {name:<25} {col_type:<15} {not_null:<10} {str(default_val):<15}")

        print("\n✅ Fertig!")

    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
