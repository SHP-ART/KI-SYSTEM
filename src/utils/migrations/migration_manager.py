"""
Migration Manager für automatische Datenbank-Schema-Updates
"""

import sqlite3
from pathlib import Path
from typing import List, Tuple
from loguru import logger


class MigrationManager:
    """
    Verwaltet Datenbank-Migrationen

    - Trackt ausgeführte Migrationen in schema_migrations Tabelle
    - Führt neue Migrationen automatisch beim Start aus
    - Idempotent: Kann mehrfach ausgeführt werden ohne Probleme
    """

    def __init__(self, db_path: str):
        """
        Args:
            db_path: Pfad zur SQLite-Datenbank
        """
        self.db_path = db_path
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Erstellt die schema_migrations Tabelle falls noch nicht vorhanden"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def get_applied_migrations(self) -> List[int]:
        """Gibt Liste der bereits angewendeten Migrations-Versionen zurück"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        versions = [row[0] for row in cursor.fetchall()]

        conn.close()
        return versions

    def get_pending_migrations(self) -> List[Tuple[int, str, str]]:
        """
        Gibt Liste der noch nicht angewendeten Migrationen zurück

        Returns:
            List of (version, name, sql) tuples
        """
        applied = set(self.get_applied_migrations())
        migrations_dir = Path(__file__).parent
        pending = []

        # Finde alle Migrations-Dateien
        for migration_file in sorted(migrations_dir.glob('[0-9]*.sql')):
            # Parse Version aus Dateiname (z.B. "001_add_continuous_measurements.sql")
            parts = migration_file.stem.split('_', 1)
            if len(parts) != 2:
                logger.warning(f"Invalid migration filename: {migration_file.name}")
                continue

            try:
                version = int(parts[0])
                name = parts[1]
            except ValueError:
                logger.warning(f"Invalid migration version in: {migration_file.name}")
                continue

            # Prüfe ob bereits angewendet
            if version in applied:
                continue

            # Lese SQL
            sql = migration_file.read_text()
            pending.append((version, name, sql))

        # Sortiere nach Version
        pending.sort(key=lambda x: x[0])
        return pending

    def apply_migration(self, version: int, name: str, sql: str) -> bool:
        """
        Wendet eine einzelne Migration an

        Args:
            version: Migrations-Version
            name: Migrations-Name
            sql: SQL-Code

        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Führe Migration in Transaktion aus
            cursor.executescript(sql)

            # Markiere als angewendet
            cursor.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                (version, name)
            )

            conn.commit()
            logger.info(f"✅ Applied migration {version:03d}: {name}")
            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed to apply migration {version:03d} ({name}): {e}")
            return False

        finally:
            conn.close()

    def run_migrations(self) -> int:
        """
        Führt alle ausstehenden Migrationen aus

        Returns:
            Anzahl der angewendeten Migrationen
        """
        pending = self.get_pending_migrations()

        if not pending:
            logger.debug("No pending database migrations")
            return 0

        logger.info(f"Found {len(pending)} pending database migration(s)")

        applied_count = 0
        for version, name, sql in pending:
            if self.apply_migration(version, name, sql):
                applied_count += 1
            else:
                logger.error(f"Migration {version} failed - stopping migration process")
                break

        if applied_count > 0:
            logger.info(f"✅ Successfully applied {applied_count} database migration(s)")

        return applied_count

    def get_current_version(self) -> int:
        """Gibt die aktuelle Schema-Version zurück (höchste angewendete Migration)"""
        applied = self.get_applied_migrations()
        return max(applied) if applied else 0

    def get_migration_history(self) -> List[dict]:
        """Gibt die komplette Migrations-Historie zurück"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT version, name, applied_at
            FROM schema_migrations
            ORDER BY version
        """)

        history = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return history
