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

        # Automatisierungs-Trigger (für neue Automation UI)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                trigger_time DATETIME NOT NULL,
                action TEXT NOT NULL
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

        conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

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
        """Löscht alte Daten basierend auf Retention-Policy"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=retention_days)

        cursor.execute("DELETE FROM sensor_data WHERE timestamp < ?", (cutoff_date,))
        cursor.execute("DELETE FROM external_data WHERE timestamp < ?", (cutoff_date,))
        cursor.execute("DELETE FROM decisions WHERE timestamp < ?", (cutoff_date,))

        conn.commit()
        logger.info(f"Cleaned up data older than {retention_days} days")

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

    def close(self):
        """Schließt die Datenbankverbindung"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __del__(self):
        """Destructor - schließt Verbindung"""
        self.close()
