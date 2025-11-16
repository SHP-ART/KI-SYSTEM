"""Automatische Datenbank-Wartung und Cleanup"""

import threading
import time
from datetime import datetime
from loguru import logger

from src.utils.database import Database
from src.utils.config_loader import ConfigLoader


class DatabaseMaintenanceJob:
    """Background-Job für automatische Datenbank-Wartung

    - Löscht alte Daten basierend auf Retention-Policy
    - Führt VACUUM aus zur Speicheroptimierung
    - Läuft täglich um 3:00 Uhr
    """

    def __init__(self, retention_days: int = 90, run_hour: int = 3):
        """Initialisiert den Maintenance-Job

        Args:
            retention_days: Anzahl Tage, die Daten behalten werden sollen (Standard: 90)
            run_hour: Stunde für tägliche Ausführung (0-23, Standard: 3 = 3:00 Uhr)
        """
        self.retention_days = retention_days
        self.run_hour = run_hour
        self.db = Database()
        self.running = False
        self.thread = None
        self.last_cleanup = None
        self.last_vacuum = None

        logger.info(f"Database Maintenance Job initialized: retention={retention_days} days, run_hour={run_hour}:00")

    def start(self):
        """Startet den Background-Job"""
        if self.running:
            logger.warning("Database Maintenance Job is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Database Maintenance Job started")

    def stop(self):
        """Stoppt den Background-Job"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Database Maintenance Job stopped")

    def _run_loop(self):
        """Haupt-Loop des Background-Jobs"""
        while self.running:
            try:
                current_time = datetime.now()

                # Prüfe ob es Zeit für Cleanup ist (täglich um run_hour Uhr, 30 Min Fenster)
                if current_time.hour == self.run_hour and current_time.minute < 30:
                    # Nur ausführen wenn heute noch nicht gelaufen
                    if not self.last_cleanup or self.last_cleanup.date() < current_time.date():
                        self.run_maintenance()

                # Schlafe 5 Minuten
                time.sleep(300)

            except Exception as e:
                logger.error(f"Error in database maintenance loop: {e}")
                time.sleep(60)  # Bei Fehler: 1 Minute warten

    def run_maintenance(self):
        """Führt die Wartungs-Aufgaben manuell aus"""
        logger.info("Starting database maintenance...")

        try:
            # 1. Alte Daten löschen
            logger.info(f"Cleaning up data older than {self.retention_days} days...")
            deleted_counts = self.db.cleanup_old_data(retention_days=self.retention_days)

            total_deleted = sum(deleted_counts.values())
            logger.info(f"Cleanup completed: {total_deleted} rows deleted")

            self.last_cleanup = datetime.now()

            # 2. VACUUM nur wenn viele Daten gelöscht wurden (> 1000 Zeilen)
            if total_deleted > 1000:
                logger.info("Running VACUUM to reclaim space...")
                self.db.vacuum_database()
                self.last_vacuum = datetime.now()
                logger.info("VACUUM completed")

            # 3. Zeige Datenbank-Statistiken
            db_info = self.db.get_database_size()
            logger.info(f"Database size: {db_info['file_size_mb']} MB, {db_info['total_rows']} total rows")

        except Exception as e:
            logger.error(f"Error during database maintenance: {e}")

    def get_status(self) -> dict:
        """Gibt den aktuellen Status des Jobs zurück"""
        db_info = self.db.get_database_size()

        return {
            'running': self.running,
            'retention_days': self.retention_days,
            'run_hour': self.run_hour,
            'last_cleanup': self.last_cleanup.isoformat() if self.last_cleanup else None,
            'last_vacuum': self.last_vacuum.isoformat() if self.last_vacuum else None,
            'database': db_info
        }


def start_database_maintenance(retention_days: int = None, run_hour: int = 3):
    """Convenience-Funktion zum Starten der Datenbank-Wartung

    Args:
        retention_days: Anzahl Tage für Retention (Standard: aus Config oder 90)
        run_hour: Stunde für tägliche Ausführung (Standard: 3 = 3:00 Uhr)

    Returns:
        DatabaseMaintenanceJob Instanz
    """
    # Lade Retention aus Config wenn nicht angegeben
    if retention_days is None:
        try:
            config = ConfigLoader()
            retention_days = config.get('database.retention_days', 90)
        except Exception as e:
            logger.warning(f"Could not load retention_days from config: {e}")
            retention_days = 90

    job = DatabaseMaintenanceJob(retention_days=retention_days, run_hour=run_hour)
    job.start()
    return job


if __name__ == '__main__':
    # Test: Führe Maintenance manuell aus
    job = DatabaseMaintenanceJob(retention_days=90)
    job.run_maintenance()

    # Zeige Status
    status = job.get_status()
    print(f"\n=== Database Status ===")
    print(f"File Size: {status['database']['file_size_mb']} MB")
    print(f"Total Rows: {status['database']['total_rows']}")
    print(f"\nTable Counts:")
    for table, count in status['database']['table_counts'].items():
        if count > 0:
            print(f"  {table}: {count:,}")
