"""Datenbankmanagement für historische Daten"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from loguru import logger


class Database:
    """SQLite Datenbank für Sensor- und Entscheidungsdaten"""

    def __init__(self, db_path: str = "data/ki_system.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        self._init_database()
        self._run_migrations()

    def _init_database(self):
        """Erstellt die Datenbank-Tabellen"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Sensor-Daten Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                sensor_id TEXT NOT NULL,
                sensor_type TEXT NOT NULL,
                value REAL,
                unit TEXT,
                metadata TEXT
            )
        """)

        # Externe Daten (Wetter, Strompreise)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS external_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                data_type TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """)

        # Entscheidungen und Aktionen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                device_id TEXT NOT NULL,
                decision_type TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence REAL,
                model_version TEXT,
                executed BOOLEAN DEFAULT 0,
                result TEXT
            )
        """)

        # Trainings-Historie
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                model_name TEXT NOT NULL,
                model_type TEXT NOT NULL,
                metrics TEXT,
                model_path TEXT
            )
        """)

        # Badezimmer Automatisierung - Events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bathroom_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                duration_minutes REAL,
                peak_humidity REAL,
                avg_humidity REAL,
                start_humidity REAL,
                end_humidity REAL,
                avg_temperature REAL,
                motion_detected BOOLEAN,
                door_closed BOOLEAN,
                dehumidifier_runtime_minutes REAL,
                event_type TEXT DEFAULT 'shower',
                day_of_week INTEGER,
                hour_of_day INTEGER
            )
        """)

        # Badezimmer - Detaillierte Messungen während Events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bathroom_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                timestamp DATETIME NOT NULL,
                humidity REAL,
                temperature REAL,
                motion BOOLEAN,
                dehumidifier_on BOOLEAN,
                FOREIGN KEY (event_id) REFERENCES bathroom_events(id)
            )
        """)

        # Badezimmer - Geräte-Aktionen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bathroom_device_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                event_id INTEGER,
                device_type TEXT NOT NULL,
                device_id TEXT NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                humidity_at_action REAL,
                temperature_at_action REAL,
                FOREIGN KEY (event_id) REFERENCES bathroom_events(id)
            )
        """)

        # Badezimmer - Gelernte Parameter
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bathroom_learned_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                parameter_name TEXT NOT NULL,
                parameter_value REAL NOT NULL,
                confidence REAL,
                samples_used INTEGER,
                reason TEXT
            )
        """)

        # Badezimmer - Kontinuierliche Messungen (alle 60s)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bathroom_continuous_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                humidity REAL,
                temperature REAL
            )
        """)

        # Automatisierungs-Trigger (für neue Automation UI)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                trigger_time DATETIME NOT NULL,
                action TEXT NOT NULL
            )
        """)

        # === HEIZUNGS-OPTIMIERUNG TABELLEN ===

        # Heizungs-Beobachtungen (kontinuierliche Aufzeichnung)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS heating_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                device_id TEXT NOT NULL,
                room_name TEXT,
                current_temperature REAL,
                target_temperature REAL,
                outdoor_temperature REAL,
                is_heating BOOLEAN,
                presence_detected BOOLEAN,
                window_open BOOLEAN,
                energy_price_level INTEGER,
                hour_of_day INTEGER,
                day_of_week INTEGER,
                is_weekend BOOLEAN
            )
        """)

        # KI-generierte Heizungs-Insights
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS heating_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                insight_type TEXT NOT NULL,
                device_id TEXT,
                room_name TEXT,
                recommendation TEXT NOT NULL,
                potential_saving_percent REAL,
                potential_saving_eur REAL,
                confidence REAL,
                samples_used INTEGER,
                priority TEXT DEFAULT 'medium'
            )
        """)

        # Optimierte Heizpläne
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS heating_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                device_id TEXT NOT NULL,
                room_name TEXT,
                schedule_type TEXT NOT NULL,
                day_of_week INTEGER,
                hour INTEGER,
                recommended_temperature REAL,
                reason TEXT,
                confidence REAL,
                samples_used INTEGER
            )
        """)

        # Erstelle Indizes für bessere Performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_timestamp
            ON sensor_data(timestamp, sensor_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_timestamp
            ON decisions(timestamp, device_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bathroom_events_time
            ON bathroom_events(start_time, end_time)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bathroom_measurements_event
            ON bathroom_measurements(event_id, timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_heating_observations_time
            ON heating_observations(timestamp, device_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_heating_insights_time
            ON heating_insights(timestamp, device_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_heating_schedules_device
            ON heating_schedules(device_id, day_of_week, hour)
        """)

        conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def _run_migrations(self):
        """Führt ausstehende Datenbank-Migrationen aus"""
        try:
            from src.utils.migrations import MigrationManager

            migrator = MigrationManager(str(self.db_path))
            applied_count = migrator.run_migrations()

            if applied_count > 0:
                logger.info(f"Applied {applied_count} database migration(s)")

        except Exception as e:
            logger.error(f"Error running database migrations: {e}")
            # Nicht fatal - System kann ohne Migrationen weiterlaufen

    def _get_connection(self) -> sqlite3.Connection:
        """Gibt eine Datenbankverbindung zurück"""
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False  # Erlaubt Multi-Threading für Flask
            )
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def insert_sensor_data(self, sensor_id: str, sensor_type: str,
                          value: float, unit: str = None,
                          metadata: Dict = None, timestamp: datetime = None):
        """Fügt Sensordaten hinzu"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sensor_data
            (timestamp, sensor_id, sensor_type, value, unit, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp or datetime.now(),
            sensor_id,
            sensor_type,
            value,
            unit,
            json.dumps(metadata) if metadata else None
        ))

        conn.commit()

    def insert_external_data(self, data_type: str, data: Dict, timestamp: datetime = None):
        """Fügt externe Daten hinzu (Wetter, Strompreise)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO external_data (timestamp, data_type, data)
            VALUES (?, ?, ?)
        """, (timestamp or datetime.now(), data_type, json.dumps(data)))

        conn.commit()

    def get_sensor_data_count(self) -> int:
        """Gibt die Gesamtanzahl der Sensor-Datensätze zurück"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM sensor_data")
        return cursor.fetchone()['count']

    def get_external_data_count(self) -> int:
        """Gibt die Gesamtanzahl der externen Datensätze zurück"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM external_data")
        return cursor.fetchone()['count']

    def get_latest_sensor_timestamp(self) -> Optional[datetime]:
        """Gibt den Zeitstempel der letzten Sensor-Messung zurück"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(timestamp) as latest FROM sensor_data")
        result = cursor.fetchone()
        if result and result['latest']:
            return datetime.fromisoformat(result['latest'])
        return None

    def insert_decision(self, device_id: str, decision_type: str,
                       action: str, confidence: float,
                       model_version: str = None):
        """Speichert eine Entscheidung"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO decisions
            (timestamp, device_id, decision_type, action, confidence, model_version)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            device_id,
            decision_type,
            action,
            confidence,
            model_version
        ))

        conn.commit()
        return cursor.lastrowid

    def update_decision_result(self, decision_id: int, executed: bool, result: str = None):
        """Aktualisiert das Ergebnis einer Entscheidung"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE decisions
            SET executed = ?, result = ?
            WHERE id = ?
        """, (executed, result, decision_id))

        conn.commit()

    def get_sensor_data(self, sensor_id: str = None,
                       sensor_type: str = None,
                       hours_back: int = 24,
                       limit: int = None) -> List[Dict]:
        """Holt Sensordaten der letzten X Stunden"""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(hours=hours_back)

        query = "SELECT * FROM sensor_data WHERE timestamp >= ?"
        params = [start_time]

        if sensor_id:
            query += " AND sensor_id = ?"
            params.append(sensor_id)

        if sensor_type:
            query += " AND sensor_type = ?"
            params.append(sensor_type)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            # Parse metadata JSON
            if result.get('metadata'):
                try:
                    result['metadata'] = json.loads(result['metadata'])
                except:
                    pass
            results.append(result)

        return results

    def get_sensor_data_aggregated(self, sensor_type: str,
                                   hours_back: int = 24,
                                   interval_minutes: int = 60) -> List[Dict]:
        """
        Holt aggregierte Sensordaten (Durchschnitt pro Intervall)
        Nützlich für Graphen
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(hours=hours_back)

        # SQLite nutzt strftime für Gruppierung
        query = """
            SELECT
                strftime('%Y-%m-%d %H:00:00', timestamp) as interval_time,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                COUNT(*) as sample_count
            FROM sensor_data
            WHERE timestamp >= ? AND sensor_type = ?
            GROUP BY interval_time
            ORDER BY interval_time ASC
        """

        cursor.execute(query, (start_time, sensor_type))

        return [dict(row) for row in cursor.fetchall()]

    def get_training_data(self, hours_back: int = 168) -> Dict[str, List[Dict]]:
        """
        Holt Trainingsdaten für ML-Modelle
        Standard: 168 Stunden = 1 Woche
        """
        sensor_data = self.get_sensor_data(hours_back=hours_back)

        # Gruppiere nach Sensor-Typ
        grouped_data = {}
        for record in sensor_data:
            sensor_type = record['sensor_type']
            if sensor_type not in grouped_data:
                grouped_data[sensor_type] = []
            grouped_data[sensor_type].append(record)

        return grouped_data

    def insert_training_history(self, model_name: str, model_type: str,
                               metrics: Dict, model_path: str):
        """Speichert Trainings-Historie"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO training_history
            (timestamp, model_name, model_type, metrics, model_path)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            model_name,
            model_type,
            json.dumps(metrics),
            model_path
        ))

        conn.commit()

    def cleanup_old_data(self, retention_days: int = 90):
        """Löscht alte Daten basierend auf Retention-Policy

        Args:
            retention_days: Anzahl der Tage, die Daten aufbewahrt werden sollen (Standard: 90)

        Returns:
            Dict mit Anzahl der gelöschten Zeilen pro Tabelle
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_counts = {}

        # Alte Sensor-Daten löschen
        cursor.execute("DELETE FROM sensor_data WHERE timestamp < ?", (cutoff_date,))
        deleted_counts['sensor_data'] = cursor.rowcount

        # Alte externe Daten löschen
        cursor.execute("DELETE FROM external_data WHERE timestamp < ?", (cutoff_date,))
        deleted_counts['external_data'] = cursor.rowcount

        # Alte Entscheidungen löschen
        cursor.execute("DELETE FROM decisions WHERE timestamp < ?", (cutoff_date,))
        deleted_counts['decisions'] = cursor.rowcount

        # Alte Badezimmer-Events löschen (behalte mehr Daten für Muster-Erkennung)
        bathroom_retention = max(retention_days, 180)  # Mind. 6 Monate
        bathroom_cutoff = datetime.now() - timedelta(days=bathroom_retention)
        cursor.execute("DELETE FROM bathroom_events WHERE start_time < ?", (bathroom_cutoff,))
        deleted_counts['bathroom_events'] = cursor.rowcount

        # Alte Badezimmer-Messungen löschen (nur behalten wenn Event noch existiert)
        cursor.execute("""
            DELETE FROM bathroom_measurements
            WHERE event_id NOT IN (SELECT id FROM bathroom_events)
        """)
        deleted_counts['bathroom_measurements'] = cursor.rowcount

        # Alte Badezimmer-Aktionen löschen
        cursor.execute("DELETE FROM bathroom_device_actions WHERE timestamp < ?", (bathroom_cutoff,))
        deleted_counts['bathroom_device_actions'] = cursor.rowcount

        # Alte kontinuierliche Badezimmer-Messungen löschen (normale Retention)
        cursor.execute("DELETE FROM bathroom_continuous_measurements WHERE timestamp < ?", (cutoff_date,))
        deleted_counts['bathroom_continuous_measurements'] = cursor.rowcount

        # Alte Heizungs-Beobachtungen löschen
        cursor.execute("DELETE FROM heating_observations WHERE timestamp < ?", (cutoff_date,))
        deleted_counts['heating_observations'] = cursor.rowcount

        # Alte Heizungs-Insights löschen (nur die ältesten, behalte mind. 30 Tage)
        insights_retention = max(retention_days, 30)
        insights_cutoff = datetime.now() - timedelta(days=insights_retention)
        cursor.execute("DELETE FROM heating_insights WHERE timestamp < ?", (insights_cutoff,))
        deleted_counts['heating_insights'] = cursor.rowcount

        conn.commit()

        total_deleted = sum(deleted_counts.values())
        logger.info(f"Cleaned up {total_deleted} rows older than {retention_days} days: {deleted_counts}")

        return deleted_counts

    def vacuum_database(self):
        """Optimiert die Datenbank durch VACUUM (gibt Speicher frei und reorganisiert)"""
        conn = self._get_connection()

        # VACUUM kann nicht in einer Transaktion laufen
        conn.isolation_level = None
        cursor = conn.cursor()

        logger.info("Running VACUUM on database...")
        cursor.execute("VACUUM")

        conn.isolation_level = ''
        logger.info("Database VACUUM completed")

    def get_database_size(self) -> Dict[str, Any]:
        """Gibt Informationen über die Datenbankgröße zurück

        Returns:
            Dict mit Dateigröße, Anzahl Zeilen pro Tabelle, etc.
        """
        import os

        # Dateigröße in MB
        file_size_bytes = os.path.getsize(self.db_path)
        file_size_mb = file_size_bytes / (1024 * 1024)

        conn = self._get_connection()
        cursor = conn.cursor()

        # Zähle Zeilen in jeder Tabelle
        tables = [
            'sensor_data',
            'external_data',
            'decisions',
            'training_history',
            'bathroom_events',
            'bathroom_measurements',
            'bathroom_device_actions',
            'bathroom_learned_parameters',
            'bathroom_continuous_measurements',
            'heating_observations',
            'heating_insights',
            'heating_schedules'
        ]

        table_counts = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_counts[table] = count
            except sqlite3.OperationalError:
                # Tabelle existiert nicht
                table_counts[table] = 0

        # Ältester und neuester Eintrag
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp)
            FROM sensor_data
        """)
        oldest, newest = cursor.fetchone()

        return {
            'file_size_mb': round(file_size_mb, 2),
            'file_size_bytes': file_size_bytes,
            'total_rows': sum(table_counts.values()),
            'table_counts': table_counts,
            'oldest_data': oldest,
            'newest_data': newest,
            'file_path': str(self.db_path)
        }

    # === BADEZIMMER AUTOMATISIERUNG - METHODEN ===

    def start_bathroom_event(self, humidity: float, temperature: float,
                            motion: bool, door_closed: bool) -> int:
        """Startet ein neues Badezimmer-Event (z.B. Duschen)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now()

        cursor.execute("""
            INSERT INTO bathroom_events
            (start_time, start_humidity, avg_temperature, motion_detected,
             door_closed, day_of_week, hour_of_day, event_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'shower')
        """, (
            now,
            humidity,
            temperature,
            motion,
            door_closed,
            now.weekday(),  # 0=Monday, 6=Sunday
            now.hour
        ))

        conn.commit()
        return cursor.lastrowid

    def end_bathroom_event(self, event_id: int, humidity: float,
                          dehumidifier_runtime: float = None):
        """Beendet ein Badezimmer-Event und berechnet Statistiken"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Hole Event-Daten
        cursor.execute("SELECT * FROM bathroom_events WHERE id = ?", (event_id,))
        event = cursor.fetchone()

        if not event:
            logger.warning(f"Event {event_id} nicht gefunden")
            return

        start_time = datetime.fromisoformat(event['start_time'])
        end_time = datetime.now()
        duration_minutes = (end_time - start_time).seconds / 60

        # Hole Messungen für dieses Event
        cursor.execute("""
            SELECT AVG(humidity) as avg_hum, MAX(humidity) as peak_hum
            FROM bathroom_measurements
            WHERE event_id = ?
        """, (event_id,))

        stats = cursor.fetchone()
        avg_humidity = stats['avg_hum'] if stats['avg_hum'] else event['start_humidity']
        peak_humidity = stats['peak_hum'] if stats['peak_hum'] else event['start_humidity']

        # Update Event
        cursor.execute("""
            UPDATE bathroom_events
            SET end_time = ?,
                duration_minutes = ?,
                end_humidity = ?,
                avg_humidity = ?,
                peak_humidity = ?,
                dehumidifier_runtime_minutes = ?
            WHERE id = ?
        """, (
            end_time,
            duration_minutes,
            humidity,
            avg_humidity,
            peak_humidity,
            dehumidifier_runtime,
            event_id
        ))

        conn.commit()
        logger.info(f"Event {event_id} beendet: {duration_minutes:.1f} Min, Peak: {peak_humidity:.1f}%")

    def add_bathroom_measurement(self, event_id: int, humidity: float,
                                temperature: float, motion: bool,
                                dehumidifier_on: bool):
        """Fügt eine Messung während eines Events hinzu"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bathroom_measurements
            (event_id, timestamp, humidity, temperature, motion, dehumidifier_on)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            datetime.now(),
            humidity,
            temperature,
            motion,
            dehumidifier_on
        ))

        conn.commit()

    def add_bathroom_continuous_measurement(self, humidity: float = None,
                                           temperature: float = None):
        """
        Fügt eine kontinuierliche Badezimmer-Messung hinzu (alle 60s)
        Unabhängig von Events - für Langzeit-Analyse
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bathroom_continuous_measurements
            (timestamp, humidity, temperature)
            VALUES (?, ?, ?)
        """, (
            datetime.now(),
            humidity,
            temperature
        ))

        conn.commit()

    def add_bathroom_device_action(self, device_type: str, device_id: str,
                                   action: str, reason: str,
                                   humidity: float, temperature: float,
                                   event_id: int = None):
        """Speichert eine Geräte-Aktion"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bathroom_device_actions
            (timestamp, event_id, device_type, device_id, action, reason,
             humidity_at_action, temperature_at_action)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            event_id,
            device_type,
            device_id,
            action,
            reason,
            humidity,
            temperature
        ))

        conn.commit()

    def save_learned_parameter(self, parameter_name: str, value: float,
                              confidence: float, samples_used: int, reason: str):
        """Speichert einen gelernten Parameter"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bathroom_learned_parameters
            (timestamp, parameter_name, parameter_value, confidence, samples_used, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            parameter_name,
            value,
            confidence,
            samples_used,
            reason
        ))

        conn.commit()
        logger.info(f"Learned parameter: {parameter_name}={value:.2f} (confidence: {confidence:.2f})")

    def get_learned_parameter(self, parameter_name: str,
                             min_confidence: float = 0.7) -> Optional[float]:
        """Holt den neuesten gelernten Parameter-Wert"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT parameter_value, confidence
            FROM bathroom_learned_parameters
            WHERE parameter_name = ? AND confidence >= ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (parameter_name, min_confidence))

        result = cursor.fetchone()
        return result['parameter_value'] if result else None

    def get_learned_parameter_details(self, parameter_name: str,
                                      min_confidence: float = 0.7) -> Optional[Dict]:
        """Holt Details des neuesten gelernten Parameters (inkl. Confidence, Samples)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT parameter_value, confidence, samples_used, timestamp, reason
            FROM bathroom_learned_parameters
            WHERE parameter_name = ? AND confidence >= ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (parameter_name, min_confidence))

        result = cursor.fetchone()
        if result:
            return {
                'value': result['parameter_value'],
                'confidence': result['confidence'],
                'samples_used': result['samples_used'],
                'timestamp': result['timestamp'],
                'reason': result['reason']
            }
        return None

    def reset_learned_parameters(self) -> int:
        """Löscht alle gelernten Parameter (Reset auf manuelle Werte)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM bathroom_learned_parameters")
        deleted_count = cursor.rowcount

        conn.commit()
        logger.info(f"Reset learned parameters: {deleted_count} entries deleted")
        return deleted_count

    def get_bathroom_events(self, days_back: int = 30, limit: int = None) -> List[Dict]:
        """Holt Badezimmer-Events der letzten X Tage"""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(days=days_back)

        query = """
            SELECT * FROM bathroom_events
            WHERE start_time >= ?
            ORDER BY start_time DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (start_time,))

        return [dict(row) for row in cursor.fetchall()]

    def get_sensor_data_timeseries(self, sensor_id: str, hours_back: int = 6) -> List[Dict]:
        """Holt Zeitreihen-Daten für einen Sensor"""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(hours=hours_back)

        cursor.execute("""
            SELECT timestamp, value, unit
            FROM sensor_data
            WHERE sensor_id = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (sensor_id, start_time))

        return [dict(row) for row in cursor.fetchall()]

    def get_bathroom_humidity_timeseries(self, hours_back: int = 6) -> List[Dict]:
        """Holt kontinuierliche Luftfeuchtigkeitsdaten aus bathroom_continuous_measurements

        Diese Methode ist speziell für die Live-Anzeige von Badezimmer-Luftfeuchtigkeit gedacht
        und nutzt die kontinuierlichen Messungen (alle 60s), nicht die sensor_data Tabelle.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(hours=hours_back)

        cursor.execute("""
            SELECT
                timestamp,
                humidity as value,
                '%' as unit
            FROM bathroom_continuous_measurements
            WHERE timestamp >= ?
              AND humidity IS NOT NULL
            ORDER BY timestamp ASC
        """, (start_time,))

        return [dict(row) for row in cursor.fetchall()]

    def create_manual_bathroom_event(self, start_time: datetime, end_time: datetime,
                                     peak_humidity: float, notes: str = None) -> int:
        """Erstellt ein manuelles Badezimmer-Event (z.B. nachträglich eingetragen)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        duration_minutes = (end_time - start_time).total_seconds() / 60

        cursor.execute("""
            INSERT INTO bathroom_events
            (start_time, end_time, duration_minutes, peak_humidity,
             start_humidity, avg_humidity, day_of_week, hour_of_day, event_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'manual')
        """, (
            start_time,
            end_time,
            duration_minutes,
            peak_humidity,
            peak_humidity - 10,  # Schätzung
            peak_humidity - 5,   # Schätzung
            start_time.weekday(),
            start_time.hour,
        ))

        conn.commit()
        event_id = cursor.lastrowid
        logger.info(f"Manual bathroom event created: {event_id} at {start_time}")
        return event_id

    def get_bathroom_statistics(self, days_back: int = 30) -> Dict:
        """Berechnet Statistiken für Badezimmer-Automatisierung"""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(days=days_back)

        # Event-Statistiken
        cursor.execute("""
            SELECT
                COUNT(*) as event_count,
                AVG(duration_minutes) as avg_duration,
                AVG(peak_humidity) as avg_peak_humidity,
                AVG(dehumidifier_runtime_minutes) as avg_dehumidifier_runtime
            FROM bathroom_events
            WHERE start_time >= ? AND end_time IS NOT NULL
        """, (start_time,))

        event_stats = dict(cursor.fetchone())

        # Häufigste Duschzeiten (nach Stunde)
        cursor.execute("""
            SELECT
                hour_of_day,
                COUNT(*) as count
            FROM bathroom_events
            WHERE start_time >= ?
            GROUP BY hour_of_day
            ORDER BY count DESC
            LIMIT 5
        """, (start_time,))

        peak_hours = [dict(row) for row in cursor.fetchall()]

        # Wochentags-Verteilung
        cursor.execute("""
            SELECT
                day_of_week,
                COUNT(*) as count
            FROM bathroom_events
            WHERE start_time >= ?
            GROUP BY day_of_week
            ORDER BY day_of_week
        """, (start_time,))

        weekday_distribution = [dict(row) for row in cursor.fetchall()]

        return {
            'event_stats': event_stats,
            'peak_hours': peak_hours,
            'weekday_distribution': weekday_distribution,
            'period_days': days_back
        }

    def get_bathroom_energy_stats(self, days_back: int = 30,
                                   dehumidifier_wattage: float = 400.0,
                                   heater_wattage: float = 0.0,
                                   energy_price_per_kwh: float = 0.30) -> Dict:
        """
        Berechnet Energie-Statistiken für Badezimmer-Automatisierung

        Args:
            days_back: Zeitraum in Tagen
            dehumidifier_wattage: Leistung des Luftentfeuchters in Watt (Standard: 400W)
            heater_wattage: Wird nicht verwendet (Zentralheizung nicht messbar)
            energy_price_per_kwh: Strompreis pro kWh in EUR (Standard: 0.30€)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(days=days_back)

        # Gesamte Laufzeit des Luftentfeuchters
        cursor.execute("""
            SELECT
                SUM(dehumidifier_runtime_minutes) as total_runtime_minutes,
                COUNT(*) as event_count
            FROM bathroom_events
            WHERE start_time >= ? AND dehumidifier_runtime_minutes IS NOT NULL
        """, (start_time,))

        result = cursor.fetchone()
        total_runtime_minutes = result['total_runtime_minutes'] or 0.0
        event_count = result['event_count'] or 0

        # Umrechnung in Stunden
        total_runtime_hours = total_runtime_minutes / 60.0

        # Energieverbrauch berechnen (nur Luftentfeuchter)
        dehumidifier_kwh = (total_runtime_hours * dehumidifier_wattage) / 1000.0
        dehumidifier_cost = dehumidifier_kwh * energy_price_per_kwh

        # Hinweis: Heizungskosten werden NICHT berechnet, da:
        # 1. Bei Zentralheizung nicht direkt messbar
        # 2. Temperaturanpassung im Bad hat minimalen Einfluss auf Gesamtverbrauch
        # 3. Nur der Luftentfeuchter hat einen messbaren, direkten Stromverbrauch

        # Gesamtkosten (nur Luftentfeuchter)
        total_kwh = dehumidifier_kwh
        total_cost = dehumidifier_cost

        # Vergleich: Wenn Luftentfeuchter immer an wäre (24/7)
        hours_in_period = days_back * 24
        always_on_kwh = (hours_in_period * dehumidifier_wattage) / 1000.0
        always_on_cost = always_on_kwh * energy_price_per_kwh

        # Ersparnis
        savings_kwh = always_on_kwh - dehumidifier_kwh
        savings_cost = always_on_cost - dehumidifier_cost
        savings_percent = (savings_kwh / always_on_kwh * 100) if always_on_kwh > 0 else 0

        # Durchschnitt pro Event
        avg_runtime_per_event = total_runtime_minutes / event_count if event_count > 0 else 0
        avg_cost_per_event = total_cost / event_count if event_count > 0 else 0

        return {
            'period_days': days_back,
            'event_count': event_count,
            'dehumidifier': {
                'runtime_hours': round(total_runtime_hours, 1),
                'runtime_minutes': round(total_runtime_minutes, 0),
                'kwh': round(dehumidifier_kwh, 2),
                'cost_eur': round(dehumidifier_cost, 2),
                'wattage': dehumidifier_wattage
            },
            'total': {
                'kwh': round(total_kwh, 2),
                'cost_eur': round(total_cost, 2)
            },
            'comparison_always_on': {
                'kwh': round(always_on_kwh, 1),
                'cost_eur': round(always_on_cost, 2),
                'savings_kwh': round(savings_kwh, 1),
                'savings_cost_eur': round(savings_cost, 2),
                'savings_percent': round(savings_percent, 1)
            },
            'per_event': {
                'avg_runtime_minutes': round(avg_runtime_per_event, 1),
                'avg_cost_eur': round(avg_cost_per_event, 3)
            },
            'energy_price_per_kwh': energy_price_per_kwh,
            'note': 'Nur Luftentfeuchter-Verbrauch. Heizungskosten (Zentralheizung) nicht einberechnet.'
        }

    # === HEIZUNGS-OPTIMIERUNG METHODEN ===

    def add_heating_observation(self, device_id: str, room_name: str,
                               current_temp: float, target_temp: float,
                               outdoor_temp: float, is_heating: bool,
                               presence: bool, window_open: bool,
                               energy_level: int = 2):
        """Fügt eine Heizungs-Beobachtung hinzu"""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now()

        cursor.execute("""
            INSERT INTO heating_observations
            (timestamp, device_id, room_name, current_temperature, target_temperature,
             outdoor_temperature, is_heating, presence_detected, window_open,
             energy_price_level, hour_of_day, day_of_week, is_weekend)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now,
            device_id,
            room_name,
            current_temp,
            target_temp,
            outdoor_temp,
            is_heating,
            presence,
            window_open,
            energy_level,
            now.hour,
            now.weekday(),
            now.weekday() >= 5
        ))

        conn.commit()

    def add_heating_insight(self, insight_type: str, recommendation: str,
                           device_id: str = None, room_name: str = None,
                           saving_percent: float = None, saving_eur: float = None,
                           confidence: float = 0.7, samples: int = 0,
                           priority: str = 'medium'):
        """Speichert einen KI-generierten Insight/Vorschlag"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO heating_insights
            (timestamp, insight_type, device_id, room_name, recommendation,
             potential_saving_percent, potential_saving_eur, confidence,
             samples_used, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            insight_type,
            device_id,
            room_name,
            recommendation,
            saving_percent,
            saving_eur,
            confidence,
            samples,
            priority
        ))

        conn.commit()
        logger.info(f"Heating insight: {insight_type} - {recommendation}")

    def get_latest_heating_insights(self, days_back: int = 7,
                                    min_confidence: float = 0.6,
                                    limit: int = 10) -> List[Dict]:
        """Holt die neuesten Heizungs-Insights"""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(days=days_back)

        cursor.execute("""
            SELECT * FROM heating_insights
            WHERE timestamp >= ? AND confidence >= ?
            ORDER BY timestamp DESC, priority DESC
            LIMIT ?
        """, (start_time, min_confidence, limit))

        return [dict(row) for row in cursor.fetchall()]

    def save_heating_schedule(self, device_id: str, room_name: str,
                             schedule_type: str, day_of_week: int, hour: int,
                             recommended_temp: float, reason: str,
                             confidence: float, samples: int):
        """Speichert einen optimierten Heizplan"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO heating_schedules
            (timestamp, device_id, room_name, schedule_type, day_of_week,
             hour, recommended_temperature, reason, confidence, samples_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            device_id,
            room_name,
            schedule_type,
            day_of_week,
            hour,
            recommended_temp,
            reason,
            confidence,
            samples
        ))

        conn.commit()

    def get_heating_schedule(self, device_id: str = None,
                            min_confidence: float = 0.7) -> List[Dict]:
        """Holt den optimierten Heizplan für ein Gerät"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if device_id:
            cursor.execute("""
                SELECT * FROM heating_schedules
                WHERE device_id = ? AND confidence >= ?
                ORDER BY day_of_week, hour
            """, (device_id, min_confidence))
        else:
            cursor.execute("""
                SELECT * FROM heating_schedules
                WHERE confidence >= ?
                ORDER BY device_id, day_of_week, hour
            """, (min_confidence,))

        return [dict(row) for row in cursor.fetchall()]

    # ===== Heizungs-Monitoring Methoden =====

    def add_heating_observation(self, device_id: str, room_name: str = None,
                                current_temp: float = None, target_temp: float = None,
                                is_heating: bool = False, outdoor_temp: float = None,
                                humidity: float = None, power_percentage: float = None):
        """Fügt eine Heizungsbeobachtung hinzu (für Analytics)"""
        from datetime import datetime

        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now()

        cursor.execute("""
            INSERT INTO heating_observations
            (timestamp, device_id, room_name, current_temp, target_temp,
             is_heating, outdoor_temp, humidity, hour_of_day, day_of_week, power_percentage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now,
            device_id,
            room_name,
            current_temp,
            target_temp,
            1 if is_heating else 0,
            outdoor_temp,
            humidity,
            now.hour,
            now.weekday(),
            power_percentage
        ))

        conn.commit()
        return cursor.lastrowid

    def get_heating_observations(self, days_back: int = 7, device_id: str = None,
                                 room_name: str = None) -> List[Dict]:
        """Holt Heizungsbeobachtungen für Analytics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(days=days_back)

        query = """
            SELECT
                timestamp,
                device_id,
                room_name,
                current_temp,
                target_temp,
                is_heating,
                outdoor_temp,
                humidity,
                hour_of_day,
                day_of_week,
                power_percentage
            FROM heating_observations
            WHERE timestamp >= ?
        """

        params = [start_time]

        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)

        if room_name:
            query += " AND room_name = ?"
            params.append(room_name)

        query += " ORDER BY timestamp ASC"

        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def get_heating_statistics(self, days_back: int = 30) -> Dict:
        """Berechnet Heizungs-Statistiken"""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(days=days_back)

        # Gesamt-Statistiken
        cursor.execute("""
            SELECT
                COUNT(*) as total_observations,
                SUM(CASE WHEN is_heating = 1 THEN 1 ELSE 0 END) as heating_count,
                AVG(current_temp) as avg_temp,
                AVG(target_temp) as avg_target,
                AVG(outdoor_temp) as avg_outdoor
            FROM heating_observations
            WHERE timestamp >= ?
        """, (start_time,))

        stats = dict(cursor.fetchone())

        # Raum-Statistiken
        cursor.execute("""
            SELECT
                room_name,
                COUNT(*) as observations,
                AVG(current_temp) as avg_temp,
                AVG(target_temp) as avg_target,
                SUM(CASE WHEN is_heating = 1 THEN 1 ELSE 0 END) as heating_count
            FROM heating_observations
            WHERE timestamp >= ? AND room_name IS NOT NULL
            GROUP BY room_name
        """, (start_time,))

        stats['room_stats'] = [dict(row) for row in cursor.fetchall()]

        return stats

    def cleanup_heating_observations(self, retention_days: int = 90) -> int:
        """Löscht alte Heizungsbeobachtungen"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=retention_days)

        cursor.execute("""
            DELETE FROM heating_observations
            WHERE timestamp < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        conn.commit()

        logger.info(f"Deleted {deleted_count} old heating observations (older than {retention_days} days)")
        return deleted_count

    # ===== Window Observations Methods =====

    def add_window_observation(self, device_id: str, device_name: str = None,
                                room_name: str = None, is_open: bool = False,
                                contact_alarm: bool = False):
        """Fügt eine Fenster-Beobachtung hinzu (alle 60s für Heizungsoptimierung)"""
        from datetime import datetime

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO window_observations
            (timestamp, device_id, device_name, room_name, is_open, contact_alarm)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            device_id,
            device_name,
            room_name,
            1 if is_open else 0,
            1 if contact_alarm else 0
        ))

        conn.commit()
        return cursor.lastrowid

    def get_current_open_windows(self) -> List[Dict]:
        """Holt alle aktuell geöffneten Fenster mit Dauer"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Nutze die View für effiziente Abfrage
        cursor.execute("""
            SELECT
                device_id,
                device_name,
                room_name,
                opened_at,
                last_seen,
                minutes_open
            FROM v_current_open_windows
            ORDER BY minutes_open DESC
        """)

        return [dict(row) for row in cursor.fetchall()]

    def get_window_observations(self, hours_back: int = 24, device_id: str = None,
                                room_name: str = None) -> List[Dict]:
        """Holt Fenster-Beobachtungen für Analytics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(hours=hours_back)

        query = """
            SELECT
                timestamp,
                device_id,
                device_name,
                room_name,
                is_open,
                contact_alarm
            FROM window_observations
            WHERE timestamp >= ?
        """

        params = [start_time]

        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)

        if room_name:
            query += " AND room_name = ?"
            params.append(room_name)

        query += " ORDER BY timestamp ASC"

        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def get_window_open_statistics(self, days_back: int = 7) -> Dict:
        """Berechnet Statistiken über offene Fenster (für Heizungsoptimierung)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(days=days_back)

        # Pro Raum: wie oft und wie lange waren Fenster offen
        cursor.execute("""
            WITH window_sessions AS (
                SELECT
                    device_id,
                    device_name,
                    room_name,
                    timestamp,
                    is_open,
                    LAG(is_open, 1, 0) OVER (PARTITION BY device_id ORDER BY timestamp) as prev_open
                FROM window_observations
                WHERE timestamp >= ?
            ),
            open_events AS (
                SELECT
                    device_id,
                    device_name,
                    room_name,
                    timestamp as opened_at,
                    LEAD(timestamp) OVER (PARTITION BY device_id ORDER BY timestamp) as closed_at
                FROM window_sessions
                WHERE is_open = 1 AND prev_open = 0
            )
            SELECT
                room_name,
                device_name,
                COUNT(*) as open_count,
                AVG(CAST((julianday(closed_at) - julianday(opened_at)) * 24 * 60 AS INTEGER)) as avg_duration_minutes,
                MAX(CAST((julianday(closed_at) - julianday(opened_at)) * 24 * 60 AS INTEGER)) as max_duration_minutes,
                SUM(CAST((julianday(closed_at) - julianday(opened_at)) * 24 * 60 AS INTEGER)) as total_minutes_open
            FROM open_events
            WHERE closed_at IS NOT NULL
            GROUP BY room_name, device_name
            ORDER BY total_minutes_open DESC
        """, (start_time,))

        stats = {
            'by_room': [dict(row) for row in cursor.fetchall()],
            'period_days': days_back
        }

        return stats

    def cleanup_window_observations(self, retention_days: int = 90) -> int:
        """Löscht alte Fenster-Beobachtungen"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=retention_days)

        cursor.execute("""
            DELETE FROM window_observations
            WHERE timestamp < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        conn.commit()

        logger.info(f"Deleted {deleted_count} old window observations (older than {retention_days} days)")
        return deleted_count

    def close(self):
        """Schließt die Datenbankverbindung"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __del__(self):
        """Destructor - schließt Verbindung"""
        self.close()
