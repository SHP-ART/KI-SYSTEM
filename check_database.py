#!/usr/bin/env python3
"""
Datenbank-Management Script

Dieses Script hilft dir, die Datenbank zu überprüfen, zu bereinigen und zu optimieren.

Verwendung:
    python3 check_database.py status    # Zeigt Datenbank-Status
    python3 check_database.py cleanup   # Löscht alte Daten (90 Tage)
    python3 check_database.py cleanup --days 60  # Löscht Daten älter als 60 Tage
    python3 check_database.py vacuum    # Optimiert die Datenbank
    python3 check_database.py all       # Führt Cleanup + Vacuum aus
"""

import sys
import argparse
from pathlib import Path

# Füge src zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.database import Database
from loguru import logger


def show_status(db: Database):
    """Zeigt den aktuellen Datenbank-Status"""
    print("\n" + "="*60)
    print("📊 DATENBANK STATUS")
    print("="*60)

    info = db.get_database_size()

    print(f"\n📁 Datei: {info['file_path']}")
    print(f"💾 Größe: {info['file_size_mb']} MB ({info['file_size_bytes']:,} Bytes)")
    print(f"📝 Gesamt Zeilen: {info['total_rows']:,}")

    print(f"\n📅 Zeitraum:")
    print(f"   Ältester Eintrag: {info['oldest_data'] or 'Keine Daten'}")
    print(f"   Neuester Eintrag: {info['newest_data'] or 'Keine Daten'}")

    print(f"\n📋 Zeilen pro Tabelle:")
    for table, count in sorted(info['table_counts'].items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"   {table:30s}: {count:>10,}")

    # Speicher-Empfehlung
    if info['file_size_mb'] > 100:
        print(f"\n⚠️  WARNUNG: Datenbank ist {info['file_size_mb']} MB groß!")
        print("   Empfehlung: Führe 'python3 check_database.py all' aus")
    elif info['file_size_mb'] > 50:
        print(f"\n💡 INFO: Datenbank ist {info['file_size_mb']} MB groß.")
        print("   Eventuell Cleanup empfohlen.")
    else:
        print(f"\n✅ Datenbank-Größe ist OK ({info['file_size_mb']} MB)")

    print("\n" + "="*60 + "\n")


def run_cleanup(db: Database, retention_days: int = 90):
    """Führt Datenbank-Cleanup aus"""
    print("\n" + "="*60)
    print(f"🧹 DATENBANK CLEANUP (>{retention_days} Tage)")
    print("="*60)

    print(f"\nLösche Daten älter als {retention_days} Tage...")

    deleted_counts = db.cleanup_old_data(retention_days=retention_days)

    total_deleted = sum(deleted_counts.values())

    print(f"\n✅ Cleanup abgeschlossen!")
    print(f"\nGelöschte Zeilen:")
    for table, count in sorted(deleted_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"   {table:30s}: {count:>10,}")

    print(f"\n📊 Gesamt gelöscht: {total_deleted:,} Zeilen")
    print("\n" + "="*60 + "\n")


def run_vacuum(db: Database):
    """Führt VACUUM aus (Datenbank-Optimierung)"""
    print("\n" + "="*60)
    print("🔧 DATENBANK VACUUM (Optimierung)")
    print("="*60)

    print("\nMesse Größe vor VACUUM...")
    before_info = db.get_database_size()
    before_size = before_info['file_size_mb']

    print(f"Größe vorher: {before_size} MB")
    print("\nFühre VACUUM aus (kann einige Sekunden dauern)...")

    db.vacuum_database()

    print("\nMesse Größe nach VACUUM...")
    after_info = db.get_database_size()
    after_size = after_info['file_size_mb']

    freed_mb = before_size - after_size

    print(f"\n✅ VACUUM abgeschlossen!")
    print(f"\nGröße vorher:  {before_size} MB")
    print(f"Größe nachher: {after_size} MB")
    print(f"Freigegeben:   {freed_mb:.2f} MB")

    if freed_mb > 1:
        print(f"\n💾 Super! {freed_mb:.2f} MB Speicher wurden freigegeben!")
    elif freed_mb > 0.1:
        print(f"\n✓ {freed_mb:.2f} MB Speicher freigegeben.")
    else:
        print(f"\nℹ️  Keine signifikante Speicherersparnis (Datenbank war bereits optimiert)")

    print("\n" + "="*60 + "\n")


def run_all(db: Database, retention_days: int = 90):
    """Führt Cleanup + Vacuum aus"""
    print("\n🔄 Führe vollständige Wartung aus...\n")
    run_cleanup(db, retention_days)
    run_vacuum(db)
    show_status(db)


def main():
    parser = argparse.ArgumentParser(
        description='Datenbank-Management für KI-SYSTEM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python3 check_database.py status              # Zeigt Status
  python3 check_database.py cleanup             # Cleanup mit 90 Tagen
  python3 check_database.py cleanup --days 60   # Cleanup mit 60 Tagen
  python3 check_database.py vacuum              # Optimiert Datenbank
  python3 check_database.py all                 # Cleanup + Vacuum
        """
    )

    parser.add_argument(
        'action',
        choices=['status', 'cleanup', 'vacuum', 'all'],
        help='Aktion, die ausgeführt werden soll'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Retention-Tage für Cleanup (Standard: 90)'
    )

    args = parser.parse_args()

    # Initialisiere Datenbank
    db = Database()

    # Führe Aktion aus
    if args.action == 'status':
        show_status(db)
    elif args.action == 'cleanup':
        run_cleanup(db, retention_days=args.days)
        show_status(db)
    elif args.action == 'vacuum':
        run_vacuum(db)
        show_status(db)
    elif args.action == 'all':
        run_all(db, retention_days=args.days)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        logger.exception("Error in database check")
        sys.exit(1)
