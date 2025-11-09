"""
Background Task: Automatische Heizungsdaten-Sammlung und Optimierung
- Sammelt regelmäßig Heizungsdaten
- Generiert täglich Optimierungsvorschläge
"""

import threading
import time
import json
from pathlib import Path
from datetime import datetime
from loguru import logger
from src.utils.database import Database


class HeatingDataCollector:
    """
    Background-Prozess für Heizungsdaten-Sammlung und Optimierung

    - Sammelt alle 15 Minuten Heizungsdaten
    - Generiert täglich um 4:00 Uhr Optimierungsvorschläge
    """

    def __init__(self, engine=None, interval_minutes: int = 15, optimize_at_hour: int = 4):
        """
        Args:
            engine: DecisionEngine Instanz (optional)
            interval_minutes: Intervall für Datensammlung in Minuten (default: 15)
            optimize_at_hour: Uhrzeit für tägliche Optimierung (default: 4 = 4:00 Uhr)
        """
        self.engine = engine
        self.interval_minutes = interval_minutes
        self.optimize_at_hour = optimize_at_hour
        self.running = False
        self.thread = None
        self.last_collection = None
        self.last_optimization = None
        self.db = Database()

    def start(self):
        """Startet den Background-Prozess"""
        if self.running:
            logger.warning("HeatingDataCollector is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"HeatingDataCollector started (collects every {self.interval_minutes}min, optimizes daily at {self.optimize_at_hour}:00)")

    def stop(self):
        """Stoppt den Background-Prozess"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("HeatingDataCollector stopped")

    def _run_loop(self):
        """Haupt-Loop des Background-Prozesses"""
        while self.running:
            try:
                # Datensammlung
                if self._should_collect_now():
                    self._collect_data()
                    self.last_collection = datetime.now()

                # Optimierung (täglich)
                if self._should_optimize_now():
                    self._run_optimization()
                    self.last_optimization = datetime.now()

                # Warte 1 Minute bevor nächster Check
                time.sleep(60)

            except Exception as e:
                logger.error(f"Error in HeatingDataCollector loop: {e}")
                time.sleep(60)

    def _should_collect_now(self) -> bool:
        """Prüft ob jetzt Daten gesammelt werden sollen"""
        if not self.last_collection:
            return True

        minutes_since_last = (datetime.now() - self.last_collection).seconds / 60
        return minutes_since_last >= self.interval_minutes

    def _should_optimize_now(self) -> bool:
        """Prüft ob jetzt optimiert werden soll"""
        now = datetime.now()

        # Prüfe ob bereits heute gelaufen
        if self.last_optimization:
            if self.last_optimization.date() == now.date():
                return False

        # Prüfe ob es die richtige Stunde ist
        if now.hour == self.optimize_at_hour:
            return True

        return False

    def _collect_data(self):
        """Sammelt aktuelle Heizungsdaten"""
        try:
            if not self.engine or not self.engine.platform:
                logger.debug("No engine/platform available for data collection")
                return

            from src.decision_engine.heating_optimizer import HeatingOptimizer

            optimizer = HeatingOptimizer(db=self.db)

            # Hole Außentemperatur
            outdoor_temp = None
            if self.engine.weather:
                weather_data = self.engine.weather.get_weather_data(self.engine.platform)
                if weather_data:
                    outdoor_temp = weather_data.get('temperature')

            # Sammle Daten
            result = optimizer.collect_current_state(
                platform=self.engine.platform,
                outdoor_temp=outdoor_temp
            )

            logger.debug(f"Collected {result.get('observations_count', 0)} heating observations")

        except Exception as e:
            logger.error(f"Error collecting heating data: {e}")

    def _run_optimization(self):
        """Führt die Optimierung durch"""
        try:
            from src.decision_engine.heating_optimizer import HeatingOptimizer

            optimizer = HeatingOptimizer(db=self.db)

            # Analysiere Muster
            logger.info("🤖 Analyzing heating patterns...")
            patterns = optimizer.analyze_patterns(days_back=14)

            if not patterns.get('sufficient_data'):
                logger.info(f"Not enough data for optimization: {patterns.get('message')}")
                return

            # Generiere Insights
            logger.info("💡 Generating optimization insights...")
            insights = optimizer.generate_insights(days_back=14)

            logger.info(f"✅ Generated {len(insights)} heating insights:")
            for insight in insights:
                logger.info(f"  - {insight.get('title')}: {insight.get('recommendation')}")
                if insight.get('saving_eur'):
                    logger.info(f"    Sparpotenzial: {insight.get('saving_eur')}€/Monat")

            # Speichere Optimierungs-Status
            status_file = Path('data/heating_optimization_status.json')
            status_file.parent.mkdir(parents=True, exist_ok=True)

            status = {
                'last_optimization': datetime.now().isoformat(),
                'insights_count': len(insights),
                'observations_count': patterns.get('observations_count', 0),
                'period_days': patterns.get('period_days', 14),
                'insights': insights
            }

            with open(status_file, 'w') as f:
                json.dump(status, f, indent=2)

            logger.info("✅ Heating optimization completed")

        except Exception as e:
            logger.error(f"Error in heating optimization: {e}")

    def get_status(self) -> dict:
        """Gibt den aktuellen Status zurück"""
        return {
            'running': self.running,
            'last_collection': self.last_collection.isoformat() if self.last_collection else None,
            'last_optimization': self.last_optimization.isoformat() if self.last_optimization else None,
            'interval_minutes': self.interval_minutes,
            'optimize_at_hour': self.optimize_at_hour
        }
