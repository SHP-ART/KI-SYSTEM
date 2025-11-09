"""
Flask Web Interface für KI-System
Dashboard, Einstellungen, Geräte-Übersicht, KI-Vorhersagen
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from pathlib import Path
from loguru import logger
from datetime import datetime
import sys
import subprocess
import os
import json

# Füge src zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import src  # Für Zugriff auf __version__
from src.decision_engine.engine import DecisionEngine
from src.data_collector.background_collector import BackgroundDataCollector
from src.background.bathroom_optimizer import BathroomOptimizer
from src.background.ml_auto_trainer import MLAutoTrainer
from src.background.heating_data_collector import HeatingDataCollector
from src.background.bathroom_data_collector import BathroomDataCollector
from src.background.database_maintenance import DatabaseMaintenanceJob
from src.utils.database import Database


class WebInterface:
    """Web Interface für das KI-System"""

    def __init__(self, config_path: str = None):
        """Initialisiere Flask App"""
        self.app = Flask(
            __name__,
            template_folder=str(Path(__file__).parent / 'templates'),
            static_folder=str(Path(__file__).parent / 'static')
        )
        CORS(self.app)

        # Initialisiere Decision Engine
        try:
            self.engine = DecisionEngine(config_path)
            logger.info("Decision Engine for web interface initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Decision Engine: {e}")
            self.engine = None

        # Initialisiere Database
        self.db = Database()

        # Initialisiere Background Data Collector
        self.background_collector = None
        if self.engine and self.engine.platform:
            try:
                self.background_collector = BackgroundDataCollector(
                    platform=self.engine.platform,
                    database=self.db,
                    interval_seconds=300  # 5 Minuten
                )
                logger.info("Background Data Collector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Background Collector: {e}")

        # Initialisiere Bathroom Optimizer (läuft täglich um 3:00 Uhr)
        self.bathroom_optimizer = None
        try:
            self.bathroom_optimizer = BathroomOptimizer(
                interval_hours=24,
                run_at_hour=3  # 3:00 Uhr morgens
            )
            logger.info("Bathroom Optimizer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Bathroom Optimizer: {e}")

        # Initialisiere ML Auto-Trainer (läuft täglich um 2:00 Uhr)
        self.ml_auto_trainer = None
        try:
            self.ml_auto_trainer = MLAutoTrainer(
                run_at_hour=2  # 2:00 Uhr morgens (vor Bathroom Optimizer)
            )
            logger.info("ML Auto-Trainer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ML Auto-Trainer: {e}")

        # Initialisiere Heating Data Collector (sammelt alle 15 Min, optimiert täglich um 4:00 Uhr)
        self.heating_collector = None
        try:
            self.heating_collector = HeatingDataCollector(
                engine=self.engine,
                interval_minutes=15,
                optimize_at_hour=4  # 4:00 Uhr morgens
            )
            logger.info("Heating Data Collector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Heating Data Collector: {e}")

        # Initialisiere Bathroom Data Collector (sammelt alle 60 Sekunden)
        self.bathroom_collector = None
        try:
            self.bathroom_collector = BathroomDataCollector(
                engine=self.engine,
                interval_seconds=60  # Alle 60 Sekunden
            )
            logger.info("Bathroom Data Collector initialized (60s interval)")
        except Exception as e:
            logger.error(f"Failed to initialize Bathroom Data Collector: {e}")

        # Initialisiere Database Maintenance Job (läuft täglich um 5:00 Uhr)
        self.db_maintenance = None
        try:
            # Lade Retention aus Config
            retention_days = self.engine.config.get('database.retention_days', 90) if self.engine else 90

            self.db_maintenance = DatabaseMaintenanceJob(
                retention_days=retention_days,
                run_hour=5  # 5:00 Uhr morgens (nach allen anderen Jobs)
            )
            logger.info(f"Database Maintenance Job initialized (retention: {retention_days} days)")
        except Exception as e:
            logger.error(f"Failed to initialize Database Maintenance: {e}")

        # Registriere Routen
        self._register_routes()

        # Registriere Context Processor für globale Template-Variablen
        @self.app.context_processor
        def inject_globals():
            """Stelle Version in allen Templates zur Verfügung"""
            return {
                'app_version': src.__version__
            }

    def _register_routes(self):
        """Registriere alle Flask-Routen"""

        @self.app.route('/')
        def index():
            """Hauptseite - Dashboard"""
            return render_template('dashboard.html')

        @self.app.route('/settings')
        def settings():
            """Einstellungsseite"""
            return render_template('settings.html')

        @self.app.route('/devices')
        def devices_page():
            """Geräte-Übersicht Seite"""
            return render_template('devices.html')

        @self.app.route('/automations')
        def automations_page():
            """Automatisierungs-Seite"""
            return render_template('automations.html')

        @self.app.route('/automations_new')
        def automations_new_page():
            """Neue Automatisierungs-Seite mit verbessertem UI"""
            return render_template('automations_new.html')

        @self.app.route('/rooms')
        def rooms_page():
            """Räume & Zonen Seite"""
            return render_template('rooms.html')

        @self.app.route('/analytics')
        def analytics_page():
            """Analytics & Verlaufs-Statistiken Seite"""
            return render_template('analytics.html')

        @self.app.route('/heizung')
        def heating_page():
            """Heizungssteuerung Seite"""
            return render_template('heating.html')

        @self.app.route('/luftentfeuchten')
        def bathroom_page():
            """Badezimmer Automatisierung Seite"""
            return render_template('luftentfeuchten.html')

        # === API Endpunkte ===

        @self.app.route('/api/status')
        def api_status():
            """API: Aktueller System-Status"""
            if not self.engine:
                return jsonify({'error': 'Engine not initialized'}), 500

            try:
                state = self.engine.collect_current_state()

                # Hole Wettervorhersage
                forecast = None
                try:
                    forecast_data = self.engine.weather.get_forecast()
                    if forecast_data:
                        forecast = forecast_data.get('forecasts', [])
                except Exception as e:
                    logger.warning(f"Could not get weather forecast: {e}")

                return jsonify({
                    'timestamp': state.get('timestamp'),
                    'temperature': {
                        'indoor': state.get('current_temperature'),
                        'outdoor': state.get('outdoor_temperature'),
                        'feels_like': state.get('feels_like'),
                        'humidity': state.get('humidity')
                    },
                    'environment': {
                        'brightness': state.get('brightness'),
                        'motion_detected': state.get('motion_detected'),
                        'weather': state.get('weather_condition'),
                        'weather_description': state.get('weather_description')
                    },
                    'weather': {
                        'condition': state.get('weather_condition'),
                        'description': state.get('weather_description'),
                        'temperature': state.get('outdoor_temperature'),
                        'feels_like': state.get('feels_like'),
                        'humidity': state.get('humidity'),
                        'wind_speed': state.get('wind_speed'),
                        'pressure': state.get('pressure'),
                        'clouds': state.get('clouds'),
                        'forecast': forecast
                    },
                    'energy': {
                        'price': state.get('energy_price'),
                        'price_level': state.get('energy_price_level'),
                        'consumption': state.get('power_consumption')
                    }
                })
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/devices')
        def api_devices():
            """API: Liste aller Geräte"""
            if not self.engine:
                return jsonify({'error': 'Engine not initialized'}), 500

            try:
                # Hole alle Geräte vom Platform Collector
                platform = self.engine.platform

                devices = []

                # Hole verschiedene Gerätetypen
                for domain in ['light', 'climate', 'switch', 'sensor']:
                    try:
                        entity_ids = platform.get_all_entities(domain)
                        states = platform.get_states(entity_ids)

                        for entity_id, state_data in states.items():
                            device_data = {
                                'id': entity_id,
                                'entity_id': entity_id,
                                'name': state_data.get('attributes', {}).get('friendly_name', entity_id),
                                'domain': domain,
                                'state': state_data.get('state'),
                                'attributes': state_data.get('attributes', {}),
                                'last_updated': state_data.get('last_updated')
                            }

                            # Für Climate/Heizgeräte: Extrahiere Temperaturen
                            if domain == 'climate':
                                capabilities = state_data.get('attributes', {}).get('capabilities', {})

                                # Aktuelle Temperatur
                                if 'measure_temperature' in capabilities:
                                    current_temp = capabilities['measure_temperature'].get('value')
                                    if current_temp is not None:
                                        device_data['current_temperature'] = current_temp
                                        if 'attributes' not in device_data:
                                            device_data['attributes'] = {}
                                        device_data['attributes']['current_temperature'] = current_temp

                                # Zieltemperatur
                                if 'target_temperature' in capabilities:
                                    target_temp = capabilities['target_temperature'].get('value')
                                    if target_temp is not None:
                                        device_data['target_temperature'] = target_temp
                                        if 'attributes' not in device_data:
                                            device_data['attributes'] = {}
                                        device_data['attributes']['temperature'] = target_temp

                                # Zone/Raum
                                zone = state_data.get('attributes', {}).get('zone')
                                if zone:
                                    device_data['zone'] = zone

                                # Capabilities Object für erweiterte Infos
                                device_data['capabilitiesObj'] = capabilities

                            devices.append(device_data)
                    except Exception as e:
                        logger.warning(f"Error getting {domain} devices: {e}")

                return jsonify({'devices': devices, 'count': len(devices)})

            except Exception as e:
                logger.error(f"Error getting devices: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/devices/<device_id>/control', methods=['POST'])
        def api_control_device(device_id):
            """API: Gerät steuern"""
            if not self.engine:
                return jsonify({'error': 'Engine not initialized'}), 500

            try:
                data = request.json
                action = data.get('action')  # 'turn_on', 'turn_off', 'set_temperature'
                platform = self.engine.platform

                if action == 'turn_on':
                    brightness = data.get('brightness')
                    result = platform.turn_on(device_id, brightness=brightness)
                elif action == 'turn_off':
                    result = platform.turn_off(device_id)
                elif action == 'set_temperature':
                    temp = data.get('temperature')
                    result = platform.set_temperature(device_id, temp)
                else:
                    return jsonify({'error': 'Unknown action'}), 400

                return jsonify({
                    'success': result,
                    'device_id': device_id,
                    'action': action
                })

            except Exception as e:
                logger.error(f"Error controlling device: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/predictions')
        def api_predictions():
            """API: KI-Vorhersagen und Empfehlungen"""
            if not self.engine:
                return jsonify({'error': 'Engine not initialized'}), 500

            try:
                # Hole aktuelle Empfehlungen
                recommendations = self.engine.get_recommendations()

                # Konvertiere Liste zu Dict wenn nötig
                if isinstance(recommendations, list):
                    recommendations = {'general': recommendations}

                # Hole aktuellen State für intelligente Vorhersagen
                state = self.engine.collect_current_state()

                # === BELEUCHTUNG ===
                lighting_actions = []
                lighting_confidence = 0.0
                lighting_status = 'optimal'

                # Prüfe Helligkeit
                brightness = state.get('sensors', {}).get('brightness')
                hour = datetime.now().hour

                if brightness is not None:
                    if brightness < 100 and 6 <= hour < 22:
                        lighting_actions.append(f'Helligkeit niedrig ({brightness} lux) - Lichter könnten eingeschaltet werden')
                        lighting_confidence = 0.85
                        lighting_status = 'action_recommended'
                    elif brightness > 800:
                        lighting_actions.append(f'Sehr hell ({brightness} lux) - Lichter können ausgeschaltet bleiben')
                        lighting_confidence = 0.90
                        lighting_status = 'optimal'
                    else:
                        lighting_confidence = 0.75
                        lighting_status = 'optimal'
                else:
                    lighting_confidence = 0.50

                # Nachtmodus
                if hour < 6 or hour >= 22:
                    lighting_actions.append('🌙 Nachtmodus: Gedimmte Beleuchtung empfohlen')
                    lighting_confidence = max(lighting_confidence, 0.80)

                # === HEIZUNG ===
                heating_actions = []
                heating_confidence = 0.0
                heating_status = 'optimal'

                outdoor_temp = state.get('weather', {}).get('temperature')
                indoor_temp = state.get('sensors', {}).get('temperature')
                energy_price = state.get('energy', {}).get('current_price')

                if outdoor_temp is not None and indoor_temp is not None:
                    temp_diff = indoor_temp - outdoor_temp

                    if outdoor_temp < 10:
                        if indoor_temp < 20:
                            heating_actions.append(f'Innentemperatur niedrig ({indoor_temp:.1f}°C) - Heizung hochdrehen empfohlen')
                            heating_confidence = 0.85
                            heating_status = 'action_recommended'
                        elif indoor_temp > 23:
                            heating_actions.append(f'Komfortable Temperatur ({indoor_temp:.1f}°C) - Heizung kann reduziert werden')
                            heating_confidence = 0.80
                            heating_status = 'savings_possible'
                        else:
                            heating_actions.append(f'Temperatur optimal ({indoor_temp:.1f}°C)')
                            heating_confidence = 0.90
                            heating_status = 'optimal'
                    elif outdoor_temp > 18:
                        heating_actions.append(f'Mildes Wetter ({outdoor_temp:.1f}°C) - Heizung kann ausgeschaltet bleiben')
                        heating_confidence = 0.95
                        heating_status = 'optimal'
                    else:
                        heating_confidence = 0.70

                    # Energiepreis-Hinweis
                    if energy_price:
                        if energy_price < 0.20:
                            heating_actions.append(f'💚 Günstiger Strompreis ({energy_price:.3f}€/kWh) - guter Zeitpunkt zum Heizen')
                        elif energy_price > 0.35:
                            heating_actions.append(f'💸 Hoher Strompreis ({energy_price:.3f}€/kWh) - Heizung wenn möglich reduzieren')
                            heating_status = 'savings_possible'
                else:
                    heating_confidence = 0.50

                # === ENERGIE-OPTIMIERUNG ===
                energy_optimization = ''
                savings_potential = '0%'
                energy_confidence = 0.0
                energy_status = 'optimal'

                if energy_price:
                    if energy_price < 0.20:
                        energy_optimization = f'💚 Niedrige Energiepreise ({energy_price:.3f}€/kWh) - guter Zeitpunkt für energieintensive Geräte'
                        savings_potential = '20%'
                        energy_confidence = 0.85
                        energy_status = 'opportunity'
                    elif energy_price < 0.30:
                        energy_optimization = f'Moderate Energiepreise ({energy_price:.3f}€/kWh) - normale Nutzung empfohlen'
                        savings_potential = '10%'
                        energy_confidence = 0.75
                        energy_status = 'optimal'
                    else:
                        energy_optimization = f'💸 Hohe Energiepreise ({energy_price:.3f}€/kWh) - nicht-essentielle Geräte später nutzen'
                        savings_potential = '25%'
                        energy_confidence = 0.90
                        energy_status = 'savings_recommended'
                else:
                    energy_optimization = 'Energiepreis-Daten nicht verfügbar'
                    savings_potential = '0%'
                    energy_confidence = 0.50
                    energy_status = 'unknown'

                # Presence-basierte Empfehlungen
                if state.get('presence', {}).get('count', 0) == 0:
                    lighting_actions.append('🏠 Niemand zuhause - alle Lichter ausschalten empfohlen')
                    heating_actions.append('🏠 Niemand zuhause - Heizung auf Abwesenheitsmodus setzen')
                    lighting_status = 'savings_possible'
                    heating_status = 'savings_possible'

                predictions = {
                    'lighting': {
                        'suggested_actions': lighting_actions,
                        'confidence': lighting_confidence,
                        'status': lighting_status,
                        'reasoning': f'Basierend auf Helligkeit ({brightness if brightness else "unbekannt"} lux), Tageszeit ({hour}:00) und Präsenz'
                    },
                    'heating': {
                        'suggested_actions': heating_actions,
                        'confidence': heating_confidence,
                        'status': heating_status,
                        'reasoning': f'Außen: {outdoor_temp if outdoor_temp else "?"}°C, Innen: {indoor_temp if indoor_temp else "?"}°C, Energiepreis: {f"{energy_price:.3f}€/kWh" if energy_price else "unbekannt"}'
                    },
                    'energy': {
                        'optimization': energy_optimization,
                        'savings_potential': savings_potential,
                        'confidence': energy_confidence,
                        'status': energy_status
                    }
                }

                return jsonify({
                    'predictions': predictions,
                    'recommendations': recommendations,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Error getting predictions: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/connection-test')
        def api_connection_test():
            """API: Verbindungstest"""
            if not self.engine:
                return jsonify({'error': 'Engine not initialized'}), 500

            try:
                results = self.engine.test_connection()
                return jsonify({
                    'results': results,
                    'all_ok': all(results.values()),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error testing connection: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/config', methods=['GET', 'POST'])
        def api_config():
            """API: Konfiguration lesen/schreiben"""
            if not self.engine:
                return jsonify({'error': 'Engine not initialized'}), 500

            if request.method == 'GET':
                # Hole aktuelle Konfiguration
                config = {
                    'platform_type': self.engine.config.get('platform.type'),
                    'data_collection_interval': self.engine.config.get('data_collection.interval_seconds'),
                    'decision_mode': self.engine.config.get('decision_engine.mode'),
                    'confidence_threshold': self.engine.config.get('decision_engine.confidence_threshold')
                }
                return jsonify(config)

            elif request.method == 'POST':
                # Update Konfiguration
                # TODO: Implementiere Config-Update
                return jsonify({'success': True, 'message': 'Config update coming soon'})

        # === Settings APIs ===

        @self.app.route('/api/settings/general', methods=['GET'])
        def api_settings_general_get():
            """API: Allgemeine Einstellungen laden"""
            try:
                import json
                from pathlib import Path

                settings_file = Path('data/settings_general.json')

                if settings_file.exists():
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                    return jsonify(settings)
                else:
                    # Rückgabe von defaults wenn keine Datei existiert
                    return jsonify({
                        'data_collection': {
                            'interval': 300,
                            'weather_enabled': True,
                            'energy_prices_enabled': False
                        },
                        'decision_engine': {
                            'mode': 'learning',
                            'confidence_threshold': 0.7
                        }
                    })

            except Exception as e:
                logger.error(f"Error loading general settings: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/settings/data-collection', methods=['POST'])
        def api_settings_data_collection():
            """API: Datensammlungs-Einstellungen speichern"""
            try:
                import json
                from pathlib import Path

                data = request.json

                # Validierung
                if 'collection_interval' in data:
                    interval = int(data['collection_interval'])
                    if interval < 60 or interval > 3600:
                        return jsonify({'error': 'Intervall muss zwischen 60 und 3600 Sekunden liegen'}), 400

                # Speichere in data/settings_general.json
                settings_file = Path('data/settings_general.json')
                settings = {}

                if settings_file.exists():
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)

                settings['data_collection'] = {
                    'interval': data.get('collection_interval', 300),
                    'weather_enabled': data.get('enable_weather', True),
                    'energy_prices_enabled': data.get('enable_energy_prices', False),
                    'updated_at': datetime.now().isoformat()
                }

                settings_file.parent.mkdir(parents=True, exist_ok=True)
                with open(settings_file, 'w') as f:
                    json.dump(settings, f, indent=2)

                logger.info(f"Data collection settings updated: {settings['data_collection']}")

                return jsonify({
                    'success': True,
                    'message': 'Datensammlungs-Einstellungen gespeichert'
                })

            except Exception as e:
                logger.error(f"Error saving data collection settings: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/settings/decision-engine', methods=['POST'])
        def api_settings_decision_engine():
            """API: Entscheidungs-Engine-Einstellungen speichern"""
            try:
                import json
                from pathlib import Path

                data = request.json

                # Validierung
                decision_mode = data.get('decision_mode', 'learning')
                if decision_mode not in ['auto', 'learning', 'manual']:
                    return jsonify({'error': 'Ungültiger Modus. Erlaubt: auto, learning, manual'}), 400

                confidence_threshold = float(data.get('confidence_threshold', 0.7))
                if confidence_threshold < 0 or confidence_threshold > 1:
                    return jsonify({'error': 'Konfidenz-Schwellwert muss zwischen 0 und 1 liegen'}), 400

                # Speichere in data/settings_general.json
                settings_file = Path('data/settings_general.json')
                settings = {}

                if settings_file.exists():
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)

                settings['decision_engine'] = {
                    'mode': decision_mode,
                    'confidence_threshold': confidence_threshold,
                    'updated_at': datetime.now().isoformat()
                }

                settings_file.parent.mkdir(parents=True, exist_ok=True)
                with open(settings_file, 'w') as f:
                    json.dump(settings, f, indent=2)

                logger.info(f"Decision engine settings updated: {settings['decision_engine']}")

                return jsonify({
                    'success': True,
                    'message': 'Entscheidungs-Engine-Einstellungen gespeichert'
                })

            except Exception as e:
                logger.error(f"Error saving decision engine settings: {e}")
                return jsonify({'error': str(e)}), 500

        # === ML Training Status API ===

        @self.app.route('/api/ml/status', methods=['GET'])
        def api_ml_status():
            """API: ML Training Status abrufen"""
            try:
                import json
                from pathlib import Path
                from datetime import datetime

                # Lade Training Status
                status_file = Path('data/ml_training_status.json')
                if status_file.exists():
                    with open(status_file, 'r') as f:
                        training_status = json.load(f)
                else:
                    training_status = {
                        'lighting_trained': False,
                        'lighting_last_trained': None,
                        'temperature_trained': False,
                        'temperature_last_trained': None
                    }

                # Zähle verfügbare Daten
                lighting_count = 0
                temp_count = 0
                days_of_data = 0

                try:
                    # Lighting events
                    result = self.db.execute(
                        "SELECT COUNT(*) as count FROM decisions WHERE device_id LIKE '%light%' OR device_id LIKE '%lamp%'"
                    )
                    lighting_count = result[0]['count'] if result else 0

                    # Temperature readings
                    result = self.db.execute(
                        "SELECT COUNT(*) as count FROM sensor_data WHERE sensor_id LIKE '%temp%' OR sensor_id LIKE '%temperature%'"
                    )
                    temp_count = result[0]['count'] if result else 0

                    # Days of data
                    result = self.db.execute(
                        "SELECT MIN(timestamp) as first_reading FROM sensor_data"
                    )
                    if result and result[0]['first_reading']:
                        first_reading = datetime.fromisoformat(result[0]['first_reading'])
                        days_of_data = (datetime.now() - first_reading).days
                except Exception as e:
                    logger.warning(f"Could not count ML data: {e}")

                # Check if models exist
                lighting_model_exists = Path('models/lighting_model.pkl').exists()
                temp_model_exists = Path('models/temperature_model.pkl').exists()

                return jsonify({
                    'lighting': {
                        'trained': lighting_model_exists or training_status.get('lighting_trained', False),
                        'last_trained': training_status.get('lighting_last_trained'),
                        'data_count': lighting_count,
                        'required': 100,
                        'ready': lighting_count >= 100 and days_of_data >= 3
                    },
                    'temperature': {
                        'trained': temp_model_exists or training_status.get('temperature_trained', False),
                        'last_trained': training_status.get('temperature_last_trained'),
                        'data_count': temp_count,
                        'required': 200,
                        'ready': temp_count >= 200 and days_of_data >= 3
                    },
                    'auto_trainer': {
                        'enabled': True,  # TODO: Load from config
                        'run_hour': 2,     # TODO: Load from config
                        'last_run': None   # TODO: Load from status
                    },
                    'days_of_data': days_of_data
                })

            except Exception as e:
                logger.error(f"Error getting ML status: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/ml/train', methods=['POST'])
        def api_ml_train():
            """API: Manuelles ML Training starten"""
            try:
                data = request.json
                model_type = data.get('model', 'all')  # 'lighting', 'temperature', or 'all'

                result_msg = []

                # Training für Auto-Trainer delegieren
                if self.ml_auto_trainer:
                    logger.info(f"Manual training requested for: {model_type}")

                    if model_type in ['lighting', 'all']:
                        success = self.ml_auto_trainer._train_lighting_model()
                        if success:
                            result_msg.append("✓ Lighting Model erfolgreich trainiert")
                        else:
                            result_msg.append("✗ Lighting Model Training fehlgeschlagen (evtl. nicht genug Daten)")

                    if model_type in ['temperature', 'all']:
                        success = self.ml_auto_trainer._train_temperature_model()
                        if success:
                            result_msg.append("✓ Temperature Model erfolgreich trainiert")
                        else:
                            result_msg.append("✗ Temperature Model Training fehlgeschlagen (evtl. nicht genug Daten)")

                    return jsonify({
                        'success': True,
                        'message': '\n'.join(result_msg) if result_msg else 'Training abgeschlossen'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'ML Auto-Trainer nicht verfügbar'
                    }), 500

            except Exception as e:
                logger.error(f"Error during manual training: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/ml/training-history', methods=['GET'])
        def api_ml_training_history():
            """API: Training History abrufen"""
            try:
                history = []
                result = self.db.execute(
                    "SELECT timestamp, model_name, accuracy, samples_used, training_time FROM training_history ORDER BY timestamp DESC LIMIT 20"
                )
                for row in result:
                    history.append({
                        'timestamp': row['timestamp'],
                        'model': row['model_name'],
                        'accuracy': round(row['accuracy'], 3) if row['accuracy'] else 0,
                        'samples': row['samples_used'],
                        'time': round(row['training_time'], 2) if row['training_time'] else 0
                    })

                return jsonify({'history': history})

            except Exception as e:
                logger.warning(f"Could not get training history: {e}")
                return jsonify({'history': []})

        @self.app.route('/api/sensors/available', methods=['GET'])
        def api_get_available_sensors():
            """API: Hole alle verfügbaren Sensoren"""
            if not self.engine:
                return jsonify({'error': 'Engine not initialized'}), 500

            try:
                # Hole alle Temperatur- und Luftfeuchtigkeit-Sensoren
                temp_sensors = self.engine._get_all_temperature_sensors()
                humidity_sensors = self.engine._get_all_humidity_sensors()

                # Hole Device-Details
                temp_details = []
                for sensor_id in temp_sensors:
                    state = self.engine.platform.get_state(sensor_id)
                    if state:
                        temp_details.append({
                            'id': sensor_id,
                            'name': state.get('attributes', {}).get('friendly_name', sensor_id),
                            'zone': state.get('attributes', {}).get('zone'),
                            'current_value': self.engine._extract_temperature_value(state)
                        })

                humidity_details = []
                for sensor_id in humidity_sensors:
                    state = self.engine.platform.get_state(sensor_id)
                    if state:
                        humidity_details.append({
                            'id': sensor_id,
                            'name': state.get('attributes', {}).get('friendly_name', sensor_id),
                            'zone': state.get('attributes', {}).get('zone'),
                            'current_value': self.engine._extract_humidity_value(state)
                        })

                return jsonify({
                    'temperature_sensors': temp_details,
                    'humidity_sensors': humidity_details
                })

            except Exception as e:
                logger.error(f"Error getting available sensors: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/sensors/config', methods=['GET', 'POST'])
        def api_sensor_config():
            """API: Sensor-Konfiguration verwalten"""
            import json
            from pathlib import Path

            config_file = Path('data/sensor_config.json')

            if request.method == 'GET':
                # Lade aktuelle Konfiguration
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                else:
                    config = {
                        'temperature_sensors': [],
                        'humidity_sensors': []
                    }

                return jsonify(config)

            elif request.method == 'POST':
                # Speichere neue Konfiguration
                try:
                    data = request.json
                    temp_sensors = data.get('temperature_sensors', [])
                    humidity_sensors = data.get('humidity_sensors', [])

                    config = {
                        'temperature_sensors': temp_sensors,
                        'humidity_sensors': humidity_sensors
                    }

                    # Erstelle data/ Verzeichnis falls nicht vorhanden
                    Path('data').mkdir(exist_ok=True)

                    # Speichere Konfiguration
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)

                    logger.info(f"Sensor config saved: {len(temp_sensors)} temp, {len(humidity_sensors)} humidity")

                    return jsonify({
                        'success': True,
                        'message': f'{len(temp_sensors)} Temperatur- und {len(humidity_sensors)} Luftfeuchtigkeits-Sensoren konfiguriert'
                    })

                except Exception as e:
                    logger.error(f"Error saving sensor config: {e}")
                    return jsonify({'error': str(e)}), 500

        # === Automation Endpunkte ===

        @self.app.route('/api/automations/config', methods=['GET'])
        def api_automations_config():
            """API: Lade Automations-Konfiguration"""
            try:
                # Lade aus Datei oder verwende Defaults
                config_file = Path('data/automations.json')
                if config_file.exists():
                    import json
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                else:
                    config = {
                        'device_config': {'learning': [], 'control': [], 'automation': []},
                        'automation_rules': {
                            'away_mode': {'enabled': False, 'timeout': 30, 'lights_off': True, 'sockets_off': True, 'heating_eco': False, 'exceptions': []},
                            'arrival_mode': {'enabled': False, 'lights_on': True, 'sockets_on': True, 'heating_comfort': False, 'time_from': '06:00', 'time_to': '23:00'},
                            'night_mode': {'enabled': False, 'time_from': '22:00', 'time_to': '06:00', 'lights_dim': True, 'no_automation': False, 'heating_lower': False}
                        }
                    }
                return jsonify(config)
            except Exception as e:
                logger.error(f"Error loading automation config: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/automations/device-config', methods=['POST'])
        def api_save_device_config():
            """API: Speichere Geräte-Konfiguration"""
            try:
                data = request.json
                device_config = data.get('device_config', {})

                # Lade aktuelle Config
                config_file = Path('data/automations.json')
                Path('data').mkdir(exist_ok=True)

                if config_file.exists():
                    import json
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                else:
                    config = {'device_config': {}, 'automation_rules': {}}

                # Update device config
                config['device_config'] = device_config

                # Speichern
                import json
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)

                logger.info(f"Device config saved: {len(device_config.get('learning', []))} learning, {len(device_config.get('control', []))} control")
                return jsonify({'success': True})

            except Exception as e:
                logger.error(f"Error saving device config: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/automations/rules', methods=['POST'])
        def api_save_automation_rules():
            """API: Speichere Automatisierungs-Regeln"""
            try:
                data = request.json
                automation_rules = data.get('automation_rules', {})

                # Lade aktuelle Config
                config_file = Path('data/automations.json')
                Path('data').mkdir(exist_ok=True)

                if config_file.exists():
                    import json
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                else:
                    config = {'device_config': {}, 'automation_rules': {}}

                # Update rules
                config['automation_rules'] = automation_rules

                # Speichern
                import json
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)

                logger.info(f"Automation rules saved: away={automation_rules.get('away_mode', {}).get('enabled')}, arrival={automation_rules.get('arrival_mode', {}).get('enabled')}")
                return jsonify({'success': True})

            except Exception as e:
                logger.error(f"Error saving automation rules: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/automations/presence', methods=['GET'])
        def api_presence_status():
            """API: Präsenz-Status ermitteln - nutzt Homey User Presence"""
            try:
                platform = self.engine.platform

                # Prüfe ob Platform Presence-Detection unterstützt
                if hasattr(platform, 'get_presence_status'):
                    # Nutze Homey's User-Presence (Smartphone-Tracking)
                    presence_data = platform.get_presence_status()

                    return jsonify({
                        'present': presence_data.get('anyone_home', False),
                        'mode': 'homey_users',
                        'users': presence_data.get('users', []),
                        'users_home': presence_data.get('users_home', 0),
                        'total_users': presence_data.get('total_users', 0)
                    })

                else:
                    # Fallback: Motion-Sensoren (für Home Assistant oder alte Homey-Versionen)
                    motion_entities = []
                    try:
                        all_entities = platform.get_all_entities('sensor')
                        states = platform.get_states(all_entities)

                        for entity_id, state_data in states.items():
                            attrs = state_data.get('attributes', {})
                            caps = attrs.get('capabilities', {})

                            # Prüfe auf Motion-Capability
                            if 'alarm_motion' in caps:
                                motion_entities.append({
                                    'id': entity_id,
                                    'motion': caps['alarm_motion'].get('value', False),
                                    'last_updated': caps['alarm_motion'].get('lastUpdated')
                                })
                    except Exception as e:
                        logger.debug(f"Error getting motion sensors: {e}")

                    # Bestimme Präsenz
                    present = False
                    last_motion = None

                    for sensor in motion_entities:
                        if sensor['motion']:
                            present = True
                            if sensor['last_updated']:
                                try:
                                    from datetime import datetime
                                    timestamp = datetime.fromtimestamp(sensor['last_updated'] / 1000)
                                    if not last_motion or timestamp > last_motion:
                                        last_motion = timestamp
                                except:
                                    pass

                    return jsonify({
                        'present': present,
                        'mode': 'motion_sensors',
                        'last_motion': last_motion.isoformat() if last_motion else None,
                        'motion_sensors': len(motion_entities)
                    })

            except Exception as e:
                logger.error(f"Error getting presence status: {e}")
                return jsonify({'error': str(e)}), 500

        # === Neue Automatisierungs-API (für automations_new.html) ===

        @self.app.route('/api/automation/scene/activate', methods=['POST'])
        def api_scene_activate():
            """API: Aktiviere eine Schnellaktion/Szene"""
            try:
                data = request.json
                scene = data.get('scene')
                actions = data.get('actions', [])

                logger.info(f"Activating scene: {scene}")

                # Führe Aktionen aus
                platform = self.engine.platform
                results = []

                for action in actions:
                    action_type = action.get('type')
                    device_target = action.get('devices')
                    command = action.get('action')
                    value = action.get('value')

                    try:
                        if device_target == 'all':
                            # Hole alle Geräte des Typs
                            if action_type == 'lights':
                                entities = platform.get_all_entities('light')
                                for entity_id in entities:
                                    if command == 'on':
                                        platform.control_device(entity_id, 'turn_on', {'brightness': value} if value else {})
                                    elif command == 'off':
                                        platform.control_device(entity_id, 'turn_off', {})
                                    elif command == 'dim':
                                        platform.control_device(entity_id, 'turn_on', {'brightness': value})
                                results.append(f"{action_type} {command}")

                            elif action_type == 'sockets':
                                entities = platform.get_all_entities('socket')
                                for entity_id in entities:
                                    if command == 'on':
                                        platform.control_device(entity_id, 'turn_on', {})
                                    elif command == 'off':
                                        platform.control_device(entity_id, 'turn_off', {})
                                results.append(f"{action_type} {command}")

                        else:
                            results.append(f"{action_type} {command} (not implemented)")

                    except Exception as e:
                        logger.warning(f"Failed to execute action {action}: {e}")
                        results.append(f"{action_type} failed")

                # Log trigger in database
                try:
                    from datetime import datetime
                    self.db.execute(
                        "INSERT INTO automation_triggers (rule_name, trigger_time, action) VALUES (?, ?, ?)",
                        (scene, datetime.now().isoformat(), f"Scene activated: {', '.join(results)}")
                    )
                except Exception as e:
                    logger.warning(f"Failed to log trigger: {e}")

                return jsonify({
                    'success': True,
                    'scene': scene,
                    'results': results
                })

            except Exception as e:
                logger.error(f"Error activating scene: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/automation/status', methods=['GET'])
        def api_automation_status():
            """API: Live-Status Dashboard"""
            try:
                from datetime import datetime, timedelta

                # Zähle aktive Regeln
                active_rules = 0
                rules_file = Path('data/automation_rules.json')
                if rules_file.exists():
                    import json
                    with open(rules_file, 'r') as f:
                        rules_data = json.load(f)
                        active_rules = len([r for r in rules_data.get('rules', []) if r.get('enabled', False)])

                # Zähle heutige Trigger
                today_triggers = 0
                try:
                    today = datetime.now().date()
                    result = self.db.execute(
                        "SELECT COUNT(*) as count FROM automation_triggers WHERE DATE(trigger_time) = ?",
                        (today.isoformat(),)
                    )
                    if result:
                        today_triggers = result[0]['count']
                except Exception as e:
                    logger.debug(f"Could not count triggers: {e}")

                # Präsenz-Status
                presence = 'unknown'
                try:
                    platform = self.engine.platform
                    if hasattr(platform, 'get_presence_status'):
                        presence_data = platform.get_presence_status()
                        presence = 'home' if presence_data.get('anyone_home', False) else 'away'
                except Exception as e:
                    logger.debug(f"Could not get presence: {e}")

                # Aktueller Modus
                current_mode = 'Normal'
                from datetime import datetime
                hour = datetime.now().hour
                if 22 <= hour or hour < 6:
                    current_mode = 'Nacht'
                elif presence == 'away':
                    current_mode = 'Abwesend'

                return jsonify({
                    'active_rules': active_rules,
                    'today_triggers': today_triggers,
                    'presence': presence,
                    'current_mode': current_mode
                })

            except Exception as e:
                logger.error(f"Error getting automation status: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/automation/triggers/recent', methods=['GET'])
        def api_automation_triggers_recent():
            """API: Letzte Auslösungen"""
            try:
                from datetime import datetime, timedelta

                # Hole letzte 10 Trigger
                triggers = []
                try:
                    result = self.db.execute(
                        "SELECT rule_name, trigger_time, action FROM automation_triggers ORDER BY trigger_time DESC LIMIT 10"
                    )
                    for row in result:
                        time_obj = datetime.fromisoformat(row['trigger_time'])
                        triggers.append({
                            'rule_name': row['rule_name'],
                            'time': time_obj.strftime('%H:%M'),
                            'action': row['action']
                        })
                except Exception as e:
                    logger.debug(f"Could not get triggers: {e}")

                return jsonify({
                    'triggers': triggers
                })

            except Exception as e:
                logger.error(f"Error getting recent triggers: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/automation/rules', methods=['GET', 'POST'])
        def api_automation_rules_list():
            """API: Regeln auflisten und erstellen"""
            import json
            rules_file = Path('data/automation_rules.json')

            if request.method == 'GET':
                # Lade alle Regeln
                if rules_file.exists():
                    with open(rules_file, 'r') as f:
                        data = json.load(f)
                        return jsonify({'rules': data.get('rules', [])})
                else:
                    return jsonify({'rules': []})

            elif request.method == 'POST':
                # Neue Regel erstellen
                new_rule = request.json

                # Generiere ID
                import uuid
                new_rule['id'] = str(uuid.uuid4())

                # Lade existierende Regeln
                if rules_file.exists():
                    with open(rules_file, 'r') as f:
                        data = json.load(f)
                else:
                    data = {'rules': []}

                # Füge neue Regel hinzu
                data['rules'].append(new_rule)

                # Speichere
                rules_file.parent.mkdir(exist_ok=True)
                with open(rules_file, 'w') as f:
                    json.dump(data, f, indent=2)

                logger.info(f"New automation rule created: {new_rule.get('name')}")

                return jsonify({
                    'success': True,
                    'rule': new_rule
                })

        @self.app.route('/api/automation/rules/<rule_id>', methods=['GET', 'PUT', 'DELETE'])
        def api_automation_rule_detail(rule_id):
            """API: Einzelne Regel abrufen, bearbeiten oder löschen"""
            import json
            rules_file = Path('data/automation_rules.json')

            if not rules_file.exists():
                return jsonify({'error': 'No rules found'}), 404

            with open(rules_file, 'r') as f:
                data = json.load(f)

            rules = data.get('rules', [])
            rule = next((r for r in rules if r['id'] == rule_id), None)

            if not rule:
                return jsonify({'error': 'Rule not found'}), 404

            if request.method == 'GET':
                return jsonify(rule)

            elif request.method == 'PUT':
                # Aktualisiere Regel
                updated_rule = request.json
                updated_rule['id'] = rule_id  # ID beibehalten

                # Ersetze Regel
                rules = [r if r['id'] != rule_id else updated_rule for r in rules]
                data['rules'] = rules

                with open(rules_file, 'w') as f:
                    json.dump(data, f, indent=2)

                logger.info(f"Automation rule updated: {updated_rule.get('name')}")

                return jsonify({
                    'success': True,
                    'rule': updated_rule
                })

            elif request.method == 'DELETE':
                # Lösche Regel
                rules = [r for r in rules if r['id'] != rule_id]
                data['rules'] = rules

                with open(rules_file, 'w') as f:
                    json.dump(data, f, indent=2)

                logger.info(f"Automation rule deleted: {rule_id}")

                return jsonify({
                    'success': True
                })

        @self.app.route('/api/automation/rules/<rule_id>/toggle', methods=['POST'])
        def api_automation_rule_toggle(rule_id):
            """API: Regel aktivieren/deaktivieren"""
            import json
            rules_file = Path('data/automation_rules.json')

            if not rules_file.exists():
                return jsonify({'error': 'No rules found'}), 404

            with open(rules_file, 'r') as f:
                data = json.load(f)

            rules = data.get('rules', [])
            rule = next((r for r in rules if r['id'] == rule_id), None)

            if not rule:
                return jsonify({'error': 'Rule not found'}), 404

            # Toggle enabled
            rule['enabled'] = not rule.get('enabled', False)

            # Speichere
            with open(rules_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Automation rule toggled: {rule.get('name')} -> {rule['enabled']}")

            return jsonify({
                'success': True,
                'enabled': rule['enabled']
            })

        # === Rooms Endpunkte ===

        @self.app.route('/api/rooms', methods=['GET', 'POST'])
        def api_rooms():
            """API: Räume verwalten"""
            import json
            rooms_file = Path('data/rooms.json')

            if request.method == 'GET':
                # Lade Räume
                if rooms_file.exists():
                    with open(rooms_file, 'r') as f:
                        data = json.load(f)
                else:
                    data = {'rooms': [], 'assignments': {}}
                return jsonify(data)

            elif request.method == 'POST':
                # Neuen Raum hinzufügen
                data = request.json
                name = data.get('name')
                icon = data.get('icon', '🏠')

                if rooms_file.exists():
                    with open(rooms_file, 'r') as f:
                        rooms_data = json.load(f)
                else:
                    rooms_data = {'rooms': [], 'assignments': {}}

                import uuid
                new_room = {
                    'id': str(uuid.uuid4()),
                    'name': name,
                    'icon': icon,
                    'type': 'custom'
                }

                rooms_data['rooms'].append(new_room)

                Path('data').mkdir(exist_ok=True)
                with open(rooms_file, 'w') as f:
                    json.dump(rooms_data, f, indent=2)

                logger.info(f"Room added: {name}")
                return jsonify({'success': True, 'room': new_room})

        def map_homey_icon_to_emoji(icon_name):
            """Konvertiert Homey Icon-Namen zu Emojis"""
            icon_mapping = {
                'livingRoom': '🛋️',
                'bedroom': '🛏️',
                'bedroomDouble': '🛏️',
                'bedroomSingle': '🛏️',
                'kitchen': '🍳',
                'bathroom': '🚿',
                'toilet': '🚽',
                'office': '💼',
                'recreationRoom': '🎮',
                'garage': '🚗',
                'garden': '🌳',
                'terrace': '🏡',
                'balcony': '🌿',
                'basement': '📦',
                'attic': '🏚️',
                'hallway': '🚪',
                'stairs': '🪜',
                'laundry': '🧺',
                'storage': '📦',
                'home': '🏠',
                'other': '📍',
                'doorClosed': '🚪',
                'sink': '💡',
                'default': '🏠'
            }
            return icon_mapping.get(icon_name, '🏠')

        @self.app.route('/api/rooms/sync-homey-zones', methods=['POST'])
        def api_sync_homey_zones():
            """API: Homey Zonen importieren"""
            try:
                import json
                platform = self.engine.platform

                # Hole Zonen von Homey
                zones = platform.get_zones()

                rooms_file = Path('data/rooms.json')
                if rooms_file.exists():
                    with open(rooms_file, 'r') as f:
                        rooms_data = json.load(f)
                else:
                    rooms_data = {'rooms': [], 'assignments': {}}

                # Konvertiere Zones zu Rooms
                imported = 0
                if isinstance(zones, dict):
                    for zone_id, zone_data in zones.items():
                        # Prüfe ob Zone schon existiert
                        if not any(r['id'] == zone_id for r in rooms_data['rooms']):
                            homey_icon = zone_data.get('icon', 'default')
                            emoji_icon = map_homey_icon_to_emoji(homey_icon)
                            rooms_data['rooms'].append({
                                'id': zone_id,
                                'name': zone_data.get('name', zone_id),
                                'icon': emoji_icon,
                                'type': 'homey'
                            })
                            imported += 1

                Path('data').mkdir(exist_ok=True)
                with open(rooms_file, 'w') as f:
                    json.dump(rooms_data, f, indent=2)

                logger.info(f"Imported {imported} Homey zones")
                return jsonify({'success': True, 'zones_imported': imported})

            except Exception as e:
                logger.error(f"Error syncing zones: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/rooms/sync-device-assignments', methods=['POST'])
        def api_sync_device_assignments():
            """API: Geräte-Zuordnungen aus Homey importieren"""
            try:
                import json
                platform = self.engine.platform

                rooms_file = Path('data/rooms.json')
                if rooms_file.exists():
                    with open(rooms_file, 'r') as f:
                        rooms_data = json.load(f)
                else:
                    rooms_data = {'rooms': [], 'assignments': {}}

                # Hole alle Geräte und extrahiere Zone-Zuordnungen
                assignments_count = 0
                for domain in ['light', 'climate', 'switch', 'sensor']:
                    try:
                        entity_ids = platform.get_all_entities(domain)
                        states = platform.get_states(entity_ids)

                        for entity_id, state_data in states.items():
                            zone_id = state_data.get('attributes', {}).get('zone')
                            if zone_id:
                                # Nur zuordnen wenn Zone als Raum existiert
                                if any(r['id'] == zone_id for r in rooms_data['rooms']):
                                    rooms_data['assignments'][entity_id] = zone_id
                                    assignments_count += 1
                    except Exception as e:
                        logger.warning(f"Error getting {domain} device assignments: {e}")

                Path('data').mkdir(exist_ok=True)
                with open(rooms_file, 'w') as f:
                    json.dump(rooms_data, f, indent=2)

                logger.info(f"Imported {assignments_count} device assignments from Homey")
                return jsonify({'success': True, 'assignments_imported': assignments_count})

            except Exception as e:
                logger.error(f"Error syncing device assignments: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/rooms/assign-device', methods=['POST'])
        def api_assign_device():
            """API: Gerät zu Raum zuordnen"""
            try:
                import json
                data = request.json
                device_id = data.get('device_id')
                room_id = data.get('room_id')

                rooms_file = Path('data/rooms.json')
                if rooms_file.exists():
                    with open(rooms_file, 'r') as f:
                        rooms_data = json.load(f)
                else:
                    rooms_data = {'rooms': [], 'assignments': {}}

                rooms_data['assignments'][device_id] = room_id

                with open(rooms_file, 'w') as f:
                    json.dump(rooms_data, f, indent=2)

                logger.info(f"Device {device_id} assigned to room {room_id}")
                return jsonify({'success': True})

            except Exception as e:
                logger.error(f"Error assigning device: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/rooms/unassign-device', methods=['POST'])
        def api_unassign_device():
            """API: Gerät von Raum entfernen"""
            try:
                import json
                data = request.json
                device_id = data.get('device_id')

                rooms_file = Path('data/rooms.json')
                if rooms_file.exists():
                    with open(rooms_file, 'r') as f:
                        rooms_data = json.load(f)

                    if device_id in rooms_data['assignments']:
                        del rooms_data['assignments'][device_id]

                        with open(rooms_file, 'w') as f:
                            json.dump(rooms_data, f, indent=2)

                logger.info(f"Device {device_id} unassigned")
                return jsonify({'success': True})

            except Exception as e:
                logger.error(f"Error unassigning device: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/rooms/control-lights', methods=['POST'])
        def api_control_room_lights():
            """API: Alle Lichter in einem Raum steuern"""
            try:
                import json
                data = request.json
                room_id = data.get('room_id')
                action = data.get('action')  # 'on' or 'off'

                # Lade Room assignments
                rooms_file = Path('data/rooms.json')
                if not rooms_file.exists():
                    return jsonify({'success': False, 'error': 'No rooms configured'}), 400

                with open(rooms_file, 'r') as f:
                    rooms_data = json.load(f)

                # Finde alle Geräte in diesem Raum
                room_devices = [device_id for device_id, rid in rooms_data['assignments'].items() if rid == room_id]

                platform = self.engine.platform
                controlled = 0

                for device_id in room_devices:
                    try:
                        # Hole Device-State um zu prüfen ob es ein Licht ist
                        state = platform.get_state(device_id)
                        if state and 'light' in device_id.lower():
                            if action == 'on':
                                platform.turn_on(device_id)
                            else:
                                platform.turn_off(device_id)
                            controlled += 1
                    except:
                        pass

                return jsonify({'success': True, 'devices_controlled': controlled})

            except Exception as e:
                logger.error(f"Error controlling room lights: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/rooms/update', methods=['POST'])
        def api_update_room():
            """API: Raum bearbeiten (Name und Icon)"""
            try:
                import json
                data = request.json
                room_id = data.get('room_id')
                new_name = data.get('name')
                new_icon = data.get('icon')

                if not room_id:
                    return jsonify({'error': 'room_id required'}), 400

                rooms_file = Path('data/rooms.json')
                if rooms_file.exists():
                    with open(rooms_file, 'r') as f:
                        rooms_data = json.load(f)

                    # Finde und aktualisiere Raum
                    for room in rooms_data['rooms']:
                        if room['id'] == room_id:
                            if new_name:
                                room['name'] = new_name
                            if new_icon:
                                room['icon'] = new_icon
                            break

                    with open(rooms_file, 'w') as f:
                        json.dump(rooms_data, f, indent=2)

                    logger.info(f"Room {room_id} updated")
                    return jsonify({'success': True})

                return jsonify({'error': 'rooms.json not found'}), 404

            except Exception as e:
                logger.error(f"Error updating room: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/rooms/delete', methods=['POST'])
        def api_delete_room():
            """API: Raum löschen"""
            try:
                import json
                data = request.json
                room_id = data.get('room_id')

                rooms_file = Path('data/rooms.json')
                if rooms_file.exists():
                    with open(rooms_file, 'r') as f:
                        rooms_data = json.load(f)

                    rooms_data['rooms'] = [r for r in rooms_data['rooms'] if r['id'] != room_id]

                    with open(rooms_file, 'w') as f:
                        json.dump(rooms_data, f, indent=2)

                logger.info(f"Room {room_id} deleted")
                return jsonify({'success': True})

            except Exception as e:
                logger.error(f"Error deleting room: {e}")
                return jsonify({'error': str(e)}), 500

        # === Analytics API Endpunkte ===

        @self.app.route('/api/analytics/temperature')
        def api_analytics_temperature():
            """API: Historische Temperatur-Daten"""
            try:
                hours = int(request.args.get('hours', 24))
                data = self.db.get_sensor_data_aggregated('temperature', hours_back=hours)

                return jsonify({
                    'success': True,
                    'data': data,
                    'hours_back': hours
                })
            except Exception as e:
                logger.error(f"Error getting temperature analytics: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/analytics/humidity')
        def api_analytics_humidity():
            """API: Historische Luftfeuchtigkeit-Daten"""
            try:
                hours = int(request.args.get('hours', 24))
                data = self.db.get_sensor_data_aggregated('humidity', hours_back=hours)

                return jsonify({
                    'success': True,
                    'data': data,
                    'hours_back': hours
                })
            except Exception as e:
                logger.error(f"Error getting humidity analytics: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/analytics/stats')
        def api_analytics_stats():
            """API: Sammel-Statistiken"""
            try:
                stats = {
                    'total_sensor_readings': self.db.get_sensor_data_count(),
                    'total_external_data': self.db.get_external_data_count(),
                    'last_collection': None,
                    'collector_running': False
                }

                if self.background_collector:
                    collector_stats = self.background_collector.get_stats()
                    stats.update(collector_stats)

                return jsonify(stats)
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/collector/status')
        def api_collector_status():
            """API: Status des Background Collectors"""
            if not self.background_collector:
                return jsonify({'running': False, 'error': 'Collector not initialized'})

            try:
                return jsonify(self.background_collector.get_stats())
            except Exception as e:
                logger.error(f"Error getting collector status: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/collector/start', methods=['POST'])
        def api_collector_start():
            """API: Starte Background Collector"""
            if not self.background_collector:
                return jsonify({'error': 'Collector not initialized'}), 500

            try:
                self.background_collector.start()
                return jsonify({'success': True, 'message': 'Collector started'})
            except Exception as e:
                logger.error(f"Error starting collector: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/collector/stop', methods=['POST'])
        def api_collector_stop():
            """API: Stoppe Background Collector"""
            if not self.background_collector:
                return jsonify({'error': 'Collector not initialized'}), 500

            try:
                self.background_collector.stop()
                return jsonify({'success': True, 'message': 'Collector stopped'})
            except Exception as e:
                logger.error(f"Error stopping collector: {e}")
                return jsonify({'error': str(e)}), 500

        # === Bathroom Automation API Endpunkte ===

        @self.app.route('/api/luftentfeuchten/config', methods=['GET', 'POST'])
        def api_bathroom_config():
            """API: Badezimmer-Konfiguration verwalten"""
            import json
            from pathlib import Path

            config_file = Path('data/luftentfeuchten_config.json')

            if request.method == 'GET':
                # Lade Konfiguration
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    return jsonify({'config': config})
                else:
                    return jsonify({'config': {'enabled': False}})

            elif request.method == 'POST':
                # Speichere Konfiguration
                try:
                    data = request.json
                    config = data.get('config', {})

                    # Speichere in Datei
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)

                    logger.info("Bathroom automation config saved")
                    return jsonify({'success': True})

                except Exception as e:
                    logger.error(f"Error saving bathroom config: {e}")
                    return jsonify({'error': str(e)}), 500

        # Cache für Bathroom Status (3 Sekunden)
        bathroom_status_cache = {'data': None, 'timestamp': 0}
        bathroom_instance_cache = {'instance': None, 'config_hash': None}

        @self.app.route('/api/luftentfeuchten/status')
        def api_bathroom_status():
            """API: Badezimmer-Status abrufen (gecached)"""
            try:
                import json
                import time
                from pathlib import Path
                from src.decision_engine.bathroom_automation import BathroomAutomation

                # Cache für 3 Sekunden
                now = time.time()
                if bathroom_status_cache['data'] and (now - bathroom_status_cache['timestamp']) < 3:
                    return jsonify(bathroom_status_cache['data'])

                config_file = Path('data/luftentfeuchten_config.json')

                if not config_file.exists():
                    result = {
                        'status': {
                            'enabled': False,
                            'shower_detected': False,
                            'dehumidifier_running': False,
                            'current_humidity': None,
                            'current_temperature': None
                        }
                    }
                    bathroom_status_cache['data'] = result
                    bathroom_status_cache['timestamp'] = now
                    return jsonify(result)

                with open(config_file, 'r') as f:
                    config = json.load(f)

                if not config.get('enabled', False):
                    result = {
                        'status': {
                            'enabled': False,
                            'shower_detected': False,
                            'dehumidifier_running': False,
                            'current_humidity': None,
                            'current_temperature': None
                        }
                    }
                    bathroom_status_cache['data'] = result
                    bathroom_status_cache['timestamp'] = now
                    return jsonify(result)

                # Prüfe ob Config geändert wurde (Hash vergleichen)
                config_hash = hash(json.dumps(config, sort_keys=True))

                if bathroom_instance_cache['config_hash'] != config_hash:
                    # Config hat sich geändert, neue Instanz erstellen
                    bathroom_instance_cache['instance'] = BathroomAutomation(config)
                    bathroom_instance_cache['config_hash'] = config_hash

                # Verwende gecachte Instanz
                bathroom = bathroom_instance_cache['instance']
                status = bathroom.get_status(self.engine.platform)

                result = {'status': status}
                bathroom_status_cache['data'] = result
                bathroom_status_cache['timestamp'] = now

                return jsonify(result)

            except Exception as e:
                logger.error(f"Error getting bathroom status: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/luftentfeuchten/test', methods=['POST'])
        def api_bathroom_test():
            """API: Badezimmer-Automatisierung testen"""
            try:
                import json
                from pathlib import Path
                from src.decision_engine.bathroom_automation import BathroomAutomation

                config_file = Path('data/luftentfeuchten_config.json')

                if not config_file.exists():
                    return jsonify({'error': 'No configuration found'}), 400

                with open(config_file, 'r') as f:
                    config = json.load(f)

                # Initialisiere und teste
                bathroom = BathroomAutomation(config)
                current_state = self.engine.collect_current_state()
                actions = bathroom.process(self.engine.platform, current_state)

                logger.info(f"Bathroom automation test: {len(actions)} actions")

                return jsonify({
                    'success': True,
                    'actions': actions,
                    'message': f'{len(actions)} Aktionen würden ausgeführt'
                })

            except Exception as e:
                logger.error(f"Error testing bathroom automation: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/luftentfeuchten/analytics')
        def api_bathroom_analytics():
            """API: Badezimmer Analytics und Statistiken"""
            try:
                import json
                from pathlib import Path
                from src.decision_engine.bathroom_automation import BathroomAutomation

                config_file = Path('data/luftentfeuchten_config.json')

                if not config_file.exists():
                    return jsonify({'error': 'No configuration found'}), 400

                with open(config_file, 'r') as f:
                    config = json.load(f)

                # Initialisiere mit Learning enabled
                bathroom = BathroomAutomation(config, enable_learning=True)

                # Hole Analytics-Daten
                days_back = int(request.args.get('days', 30))
                analytics = bathroom.get_analytics(days_back=days_back)

                return jsonify(analytics)

            except Exception as e:
                logger.error(f"Error getting bathroom analytics: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/luftentfeuchten/events')
        def api_bathroom_events():
            """API: Badezimmer Events (Historie)"""
            try:
                from src.utils.database import Database

                db = Database()
                days_back = int(request.args.get('days', 30))
                limit = int(request.args.get('limit', 100))

                events = db.get_bathroom_events(days_back=days_back, limit=limit)

                return jsonify({
                    'events': events,
                    'count': len(events),
                    'days_back': days_back
                })

            except Exception as e:
                logger.error(f"Error getting bathroom events: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/luftentfeuchten/optimize', methods=['POST'])
        def api_bathroom_optimize():
            """API: Badezimmer Parameter optimieren"""
            try:
                import json
                from pathlib import Path
                from src.decision_engine.bathroom_automation import BathroomAutomation

                config_file = Path('data/luftentfeuchten_config.json')

                if not config_file.exists():
                    return jsonify({'error': 'No configuration found'}), 400

                with open(config_file, 'r') as f:
                    config = json.load(f)

                # Initialisiere mit Learning enabled
                bathroom = BathroomAutomation(config, enable_learning=True)

                # Optimiere Parameter
                days_back = int(request.json.get('days_back', 30)) if request.json else 30
                min_confidence = float(request.json.get('min_confidence', 0.7)) if request.json else 0.7

                result = bathroom.optimize_parameters(
                    days_back=days_back,
                    min_confidence=min_confidence
                )

                if result and result.get('success'):
                    # Update config mit neuen Werten
                    config['humidity_threshold_high'] = result['new_values']['humidity_high']
                    config['humidity_threshold_low'] = result['new_values']['humidity_low']

                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)

                    logger.info("✨ Configuration updated with optimized values")

                return jsonify(result if result else {'success': False, 'reason': 'Optimization failed'})

            except Exception as e:
                logger.error(f"Error optimizing bathroom parameters: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/luftentfeuchten/live-status')
        def api_bathroom_live_status():
            """API: Live-Status aller konfigurierten Badezimmer-Sensoren und Aktoren"""
            try:
                import json
                from pathlib import Path

                config_file = Path('data/luftentfeuchten_config.json')

                if not config_file.exists():
                    return jsonify({'error': 'No configuration found', 'devices': {}}), 200

                with open(config_file, 'r') as f:
                    config = json.load(f)

                devices_status = {}

                # Humidity Sensor
                if config.get('humidity_sensor_id'):
                    sensor_id = config['humidity_sensor_id']
                    state = self.engine.platform.get_state(sensor_id)
                    if state:
                        devices_status['humidity_sensor'] = {
                            'id': sensor_id,
                            'name': state.get('attributes', {}).get('friendly_name', sensor_id),
                            'value': self.engine._extract_humidity_value(state),
                            'unit': '%',
                            'available': state.get('state', 'unknown') != 'unavailable'
                        }

                # Temperature Sensor
                if config.get('temperature_sensor_id'):
                    sensor_id = config['temperature_sensor_id']
                    state = self.engine.platform.get_state(sensor_id)
                    if state:
                        devices_status['temperature_sensor'] = {
                            'id': sensor_id,
                            'name': state.get('attributes', {}).get('friendly_name', sensor_id),
                            'value': self.engine._extract_temperature_value(state),
                            'unit': '°C',
                            'available': state.get('state', 'unknown') != 'unavailable'
                        }

                # Door Sensor
                if config.get('door_sensor_id'):
                    sensor_id = config['door_sensor_id']
                    state = self.engine.platform.get_state(sensor_id)
                    if state:
                        # alarm_contact: true = closed (contact made), false = open (contact broken)
                        caps = state.get('capabilitiesObj', {})
                        alarm_contact = caps.get('alarm_contact', {}).get('value', False)
                        devices_status['door_sensor'] = {
                            'id': sensor_id,
                            'name': state.get('name', sensor_id),
                            'value': 'closed' if alarm_contact else 'open',
                            'is_open': not alarm_contact,
                            'available': state.get('available', True)
                        }

                # Window Sensor
                if config.get('window_sensor_id'):
                    sensor_id = config['window_sensor_id']
                    state = self.engine.platform.get_state(sensor_id)
                    if state:
                        # alarm_contact: true = open, false = closed
                        caps = state.get('capabilitiesObj', {})
                        alarm_contact = caps.get('alarm_contact', {}).get('value', False)
                        devices_status['window_sensor'] = {
                            'id': sensor_id,
                            'name': state.get('name', sensor_id),
                            'value': 'open' if alarm_contact else 'closed',
                            'is_open': alarm_contact,
                            'available': state.get('available', True)
                        }

                # Motion Sensor
                if config.get('motion_sensor_id'):
                    sensor_id = config['motion_sensor_id']
                    state = self.engine.platform.get_state(sensor_id)
                    if state:
                        # alarm_motion: true = motion detected
                        caps = state.get('capabilitiesObj', {})
                        alarm_motion = caps.get('alarm_motion', {}).get('value', False)
                        devices_status['motion_sensor'] = {
                            'id': sensor_id,
                            'name': state.get('name', sensor_id),
                            'value': 'detected' if alarm_motion else 'clear',
                            'motion_detected': alarm_motion,
                            'available': state.get('available', True)
                        }

                # Dehumidifier
                if config.get('dehumidifier_id'):
                    device_id = config['dehumidifier_id']
                    state = self.engine.platform.get_state(device_id)
                    if state:
                        caps = state.get('capabilitiesObj', {})
                        onoff = caps.get('onoff', {}).get('value', False)
                        devices_status['dehumidifier'] = {
                            'id': device_id,
                            'name': state.get('name', device_id),
                            'value': 'on' if onoff else 'off',
                            'is_on': onoff,
                            'available': state.get('available', True)
                        }

                # Heater
                if config.get('heater_id'):
                    device_id = config['heater_id']
                    state = self.engine.platform.get_state(device_id)
                    if state:
                        caps = state.get('capabilitiesObj', {})
                        target_temp = caps.get('target_temperature', {}).get('value', None)
                        devices_status['heater'] = {
                            'id': device_id,
                            'name': state.get('name', device_id),
                            'value': target_temp,
                            'unit': '°C',
                            'available': state.get('available', True)
                        }

                return jsonify({'devices': devices_status})

            except Exception as e:
                logger.error(f"Error getting bathroom live status: {e}")
                return jsonify({'error': str(e), 'devices': {}}), 500

        @self.app.route('/api/luftentfeuchten/control', methods=['POST'])
        def api_bathroom_control():
            """API: Steuerung von Aktoren (Luftentfeuchter, Heizung)"""
            try:
                data = request.json
                device_type = data.get('device_type')  # 'dehumidifier' or 'heater'
                action = data.get('action')  # 'on', 'off', 'temp_up', 'temp_down'

                import json
                from pathlib import Path

                config_file = Path('data/luftentfeuchten_config.json')

                if not config_file.exists():
                    return jsonify({'error': 'No configuration found'}), 400

                with open(config_file, 'r') as f:
                    config = json.load(f)

                success = False
                message = ""

                if device_type == 'dehumidifier':
                    device_id = config.get('dehumidifier_id')
                    if not device_id:
                        return jsonify({'error': 'Dehumidifier not configured'}), 400

                    if action == 'on':
                        self.engine.platform.turn_on(device_id)
                        success = True
                        message = "Luftentfeuchter eingeschaltet"
                    elif action == 'off':
                        self.engine.platform.turn_off(device_id)
                        success = True
                        message = "Luftentfeuchter ausgeschaltet"

                elif device_type == 'heater':
                    device_id = config.get('heater_id')
                    if not device_id:
                        return jsonify({'error': 'Heater not configured'}), 400

                    # Get current temperature
                    state = self.engine.platform.get_state(device_id)
                    if state:
                        caps = state.get('capabilitiesObj', {})
                        current_temp = caps.get('target_temperature', {}).get('value', 20.0)

                        if action == 'temp_up':
                            new_temp = min(current_temp + 1, 30)  # Max 30°C
                            self.engine.platform.set_climate_temperature(device_id, new_temp)
                            success = True
                            message = f"Heizung auf {new_temp}°C erhöht"
                        elif action == 'temp_down':
                            new_temp = max(current_temp - 1, 10)  # Min 10°C
                            self.engine.platform.set_climate_temperature(device_id, new_temp)
                            success = True
                            message = f"Heizung auf {new_temp}°C gesenkt"

                if success:
                    logger.info(f"Bathroom control: {device_type} - {action}")
                    return jsonify({'success': True, 'message': message})
                else:
                    return jsonify({'error': 'Invalid action'}), 400

            except Exception as e:
                logger.error(f"Error controlling bathroom device: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/luftentfeuchten/analytics')
        def page_bathroom_analytics():
            """Seite: Badezimmer Analytics Dashboard"""
            return render_template('luftentfeuchten_analytics.html')

        @self.app.route('/api/luftentfeuchten/learned-params', methods=['GET'])
        def api_bathroom_learned_params():
            """API: Hole Details zu gelernten Parametern"""
            try:
                # Hole Details für alle relevanten Parameter
                params_info = {}
                param_names = ['humidity_threshold_high', 'humidity_threshold_low', 'dehumidifier_delay']

                for param_name in param_names:
                    details = self.db.get_learned_parameter_details(param_name, min_confidence=0.0)
                    if details:
                        params_info[param_name] = {
                            'value': details['value'],
                            'confidence': details['confidence'],
                            'samples_used': details['samples_used'],
                            'timestamp': details['timestamp'],
                            'reason': details['reason'],
                            'is_learned': True
                        }
                    else:
                        params_info[param_name] = {
                            'is_learned': False
                        }

                # Zähle Events für Info
                events_count = len(self.db.get_bathroom_events(days_back=30))

                return jsonify({
                    'learned_params': params_info,
                    'events_last_30_days': events_count,
                    'ready_for_optimization': events_count >= 5
                })

            except Exception as e:
                logger.error(f"Error getting learned params: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/luftentfeuchten/reset-learned', methods=['POST'])
        def api_bathroom_reset_learned():
            """API: Setze gelernte Parameter zurück (verwende wieder manuelle Werte)"""
            try:
                deleted_count = self.db.reset_learned_parameters()

                logger.info(f"Learned parameters reset: {deleted_count} entries deleted")

                return jsonify({
                    'success': True,
                    'message': f'{deleted_count} gelernte Parameter zurückgesetzt',
                    'deleted_count': deleted_count
                })

            except Exception as e:
                logger.error(f"Error resetting learned parameters: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/luftentfeuchten/energy-stats', methods=['GET'])
        def api_bathroom_energy_stats():
            """API: Energie & Kosten-Statistiken"""
            try:
                import json
                from pathlib import Path

                # Hole Parameter aus Query oder Config
                days_back = int(request.args.get('days', 30))

                # Lade Config für Geräte-Leistungen
                config_file = Path('data/luftentfeuchten_config.json')
                dehumidifier_wattage = 400.0  # Default
                energy_price = 0.30  # Default EUR/kWh

                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        dehumidifier_wattage = config.get('dehumidifier_wattage', 400.0)
                        energy_price = config.get('energy_price_per_kwh', 0.30)

                # Berechne Statistiken (nur Luftentfeuchter, keine Heizung)
                stats = self.db.get_bathroom_energy_stats(
                    days_back=days_back,
                    dehumidifier_wattage=dehumidifier_wattage,
                    heater_wattage=0.0,  # Zentralheizung nicht messbar
                    energy_price_per_kwh=energy_price
                )

                return jsonify(stats)

            except Exception as e:
                logger.error(f"Error getting energy stats: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/luftentfeuchten/alerts', methods=['GET'])
        def api_bathroom_alerts():
            """API: System-Gesundheits-Alerts"""
            try:
                from src.decision_engine.bathroom_analyzer import BathroomAnalyzer

                days_back = int(request.args.get('days', 7))

                analyzer = BathroomAnalyzer(self.db)
                alerts = analyzer.check_system_health(days_back=days_back)

                # Sortiere nach Severity (high > medium > low)
                severity_order = {'high': 0, 'medium': 1, 'low': 2}
                alerts.sort(key=lambda x: severity_order.get(x.get('severity', 'low'), 2))

                return jsonify({
                    'alerts': alerts,
                    'count': len(alerts),
                    'has_critical': any(a.get('severity') == 'high' for a in alerts),
                    'days_checked': days_back
                })

            except Exception as e:
                logger.error(f"Error getting bathroom alerts: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/luftentfeuchten/preview', methods=['POST'])
        def api_bathroom_preview():
            """API: Live-Preview - Was würde das System jetzt tun?"""
            try:
                from src.decision_engine.bathroom_automation import BathroomAutomation
                import json
                from pathlib import Path

                # Lade Config
                config_file = Path('data/luftentfeuchten_config.json')
                if not config_file.exists():
                    return jsonify({'error': 'No configuration found'}), 400

                with open(config_file, 'r') as f:
                    config = json.load(f)

                # Initialisiere Automation (ohne Speichern)
                bathroom = BathroomAutomation(config, enable_learning=False)

                # Hole aktuellen State
                current_state = self.engine.collect_current_state()

                # Hole Live-Sensor-Werte
                humidity = bathroom._get_humidity(self.engine.platform)
                temperature = bathroom._get_temperature(self.engine.platform)
                motion = bathroom._check_motion(self.engine.platform)
                door_closed = bathroom._check_door(self.engine.platform)

                # Simuliere Entscheidungen (ohne Ausführung)
                would_detect_shower = bathroom._detect_shower(humidity, motion, door_closed)

                # Prüfe Luftentfeuchter-Aktion
                dehumidifier_action = None
                should_turn_on_dehumidifier = (humidity and humidity > bathroom.humidity_high) or would_detect_shower
                should_turn_off_dehumidifier = humidity and humidity < bathroom.humidity_low

                if should_turn_on_dehumidifier:
                    dehumidifier_action = {
                        'action': 'turn_on',
                        'reason': f'Hohe Luftfeuchtigkeit ({humidity}% > {bathroom.humidity_high}%)',
                        'would_execute': config.get('enabled', False)
                    }
                elif should_turn_off_dehumidifier and bathroom.dehumidifier_running:
                    dehumidifier_action = {
                        'action': 'turn_off',
                        'reason': f'Luftfeuchtigkeit normalisiert ({humidity}% < {bathroom.humidity_low}%)',
                        'would_execute': config.get('enabled', False)
                    }
                else:
                    dehumidifier_action = {
                        'action': 'no_change',
                        'reason': f'Luftfeuchtigkeit OK ({humidity}%, Schwellwerte: {bathroom.humidity_low}%-{bathroom.humidity_high}%)',
                        'would_execute': False
                    }

                # Prüfe Heizungs-Aktion
                heater_action = None
                if temperature and bathroom.dehumidifier_running:
                    target = bathroom.target_temp + 1.0
                    if abs(temperature - target) > 0.5:
                        heater_action = {
                            'action': 'set_temperature',
                            'target_temperature': target,
                            'reason': f'Entfeuchtung aktiv → Heizung auf {target}°C (aktuell: {temperature}°C)',
                            'would_execute': config.get('enabled', False)
                        }

                if not heater_action and temperature:
                    heater_action = {
                        'action': 'no_change',
                        'target_temperature': bathroom.target_temp,
                        'reason': f'Keine Heizungs-Anpassung nötig (aktuell: {temperature}°C, Ziel: {bathroom.target_temp}°C)',
                        'would_execute': False
                    }

                return jsonify({
                    'current_state': {
                        'humidity': humidity,
                        'temperature': temperature,
                        'motion_detected': motion,
                        'door_closed': door_closed,
                        'shower_would_be_detected': would_detect_shower
                    },
                    'thresholds': {
                        'humidity_high': bathroom.humidity_high,
                        'humidity_low': bathroom.humidity_low,
                        'target_temperature': bathroom.target_temp
                    },
                    'actions': {
                        'dehumidifier': dehumidifier_action,
                        'heater': heater_action
                    },
                    'automation_enabled': config.get('enabled', False)
                })

            except Exception as e:
                logger.error(f"Error in bathroom preview: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/luftentfeuchten/sensor-timeseries', methods=['GET'])
        def api_bathroom_sensor_timeseries():
            """API: Zeitreihen-Daten für Luftfeuchtigkeit im Bad

            Verwendet die kontinuierlichen Messungen (alle 60s) aus bathroom_continuous_measurements
            statt der gemischten sensor_data Tabelle, um saubere Zeitreihen ohne Zickzack-Muster zu liefern.
            """
            try:
                # Hole Zeitraum aus Query-Parametern
                hours = int(request.args.get('hours', 6))

                # Hole kontinuierliche Messungen (alle 60s)
                data = self.db.get_bathroom_humidity_timeseries(hours_back=hours)

                if not data or len(data) == 0:
                    logger.info(f"No continuous humidity measurements found in last {hours} hours")

                return jsonify({
                    'source': 'bathroom_continuous_measurements',
                    'interval': '60s',
                    'hours': hours,
                    'data': data,
                    'count': len(data)
                })

            except Exception as e:
                logger.error(f"Error getting bathroom humidity timeseries: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/luftentfeuchten/manual-event', methods=['POST'])
        def api_bathroom_manual_event():
            """API: Manuelles Eintragen eines Duschereignisses"""
            try:
                data = request.json

                # Validierung
                if not data.get('start_time') or not data.get('end_time'):
                    return jsonify({'error': 'start_time and end_time are required'}), 400

                # Parse Zeitstempel
                from datetime import datetime
                start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))

                # Peak Humidity (optional, default 75%)
                peak_humidity = float(data.get('peak_humidity', 75.0))

                # Erstelle Event
                event_id = self.db.create_manual_bathroom_event(
                    start_time=start_time,
                    end_time=end_time,
                    peak_humidity=peak_humidity,
                    notes=data.get('notes')
                )

                logger.info(f"Manual bathroom event created: {event_id} by user")

                return jsonify({
                    'success': True,
                    'event_id': event_id,
                    'message': 'Duschereignis erfolgreich eingetragen'
                })

            except Exception as e:
                logger.error(f"Error creating manual bathroom event: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/luftentfeuchten/data-stats')
        def api_bathroom_data_stats():
            """API: Statistiken über gespeicherte Badezimmer-Daten"""
            try:
                conn = self.db._get_connection()
                cursor = conn.cursor()

                # Zähle Events
                cursor.execute("SELECT COUNT(*) FROM bathroom_events")
                events_count = cursor.fetchone()[0]

                # Zähle Messungen
                cursor.execute("SELECT COUNT(*) FROM bathroom_measurements")
                measurements_count = cursor.fetchone()[0]

                # Zähle Geräteaktionen
                cursor.execute("SELECT COUNT(*) FROM bathroom_device_actions")
                actions_count = cursor.fetchone()[0]

                # Zähle kontinuierliche Messungen (60s-Intervall)
                cursor.execute("SELECT COUNT(*) FROM bathroom_continuous_measurements")
                continuous_measurements_count = cursor.fetchone()[0]

                # Ältestes und neuestes Event
                cursor.execute("""
                    SELECT MIN(start_time), MAX(start_time)
                    FROM bathroom_events
                    WHERE start_time IS NOT NULL
                """)
                oldest, newest = cursor.fetchone()

                # Berechne Zeitspanne
                data_age = None
                date_range = "Keine Daten"
                if oldest and newest:
                    from datetime import datetime
                    oldest_dt = datetime.fromisoformat(oldest) if isinstance(oldest, str) else oldest
                    newest_dt = datetime.fromisoformat(newest) if isinstance(newest, str) else newest

                    # Entferne Timezone-Info falls vorhanden, um offset-naive/aware Fehler zu vermeiden
                    if oldest_dt.tzinfo is not None:
                        oldest_dt = oldest_dt.replace(tzinfo=None)
                    if newest_dt.tzinfo is not None:
                        newest_dt = newest_dt.replace(tzinfo=None)

                    days = (datetime.now() - oldest_dt).days
                    data_age = f"{days} Tage"

                    # Format: "DD.MM.YYYY - DD.MM.YYYY"
                    oldest_str = oldest_dt.strftime("%d.%m.%Y")
                    newest_str = newest_dt.strftime("%d.%m.%Y")
                    date_range = f"{oldest_str} - {newest_str}"

                return jsonify({
                    'success': True,
                    'events_count': events_count,
                    'measurements_count': measurements_count,
                    'actions_count': actions_count,
                    'continuous_measurements_count': continuous_measurements_count,
                    'data_age': data_age,
                    'date_range': date_range,
                    'oldest_date': oldest,
                    'newest_date': newest
                })

            except Exception as e:
                logger.error(f"Error fetching bathroom data stats: {e}")
                return jsonify({'error': str(e)}), 500

        # ===== Heizungs-Optimierungs-Endpoints =====

        @self.app.route('/api/heating/mode', methods=['GET', 'POST'])
        def api_heating_mode():
            """Hole oder setze Heizungs-Modus (control/optimization)"""
            mode_file = Path('data/heating_mode.json')

            if request.method == 'GET':
                # Lade aktuellen Modus
                if mode_file.exists():
                    with open(mode_file, 'r') as f:
                        data = json.load(f)
                    return jsonify(data)
                else:
                    # Default: control mode
                    return jsonify({'mode': 'control', 'description': 'Direkte Steuerung'})

            elif request.method == 'POST':
                # Setze neuen Modus
                data = request.json
                mode = data.get('mode', 'control')

                if mode not in ['control', 'optimization']:
                    return jsonify({'error': 'Invalid mode'}), 400

                mode_data = {
                    'mode': mode,
                    'description': 'Direkte Steuerung' if mode == 'control' else 'Nur Monitoring & Vorschläge',
                    'updated_at': datetime.now().isoformat()
                }

                # Speichere Modus
                mode_file.parent.mkdir(parents=True, exist_ok=True)
                with open(mode_file, 'w') as f:
                    json.dump(mode_data, f, indent=2)

                logger.info(f"Heating mode changed to: {mode}")
                return jsonify({'success': True, **mode_data})

        @self.app.route('/api/heating/insights')
        def api_heating_insights():
            """Hole KI-generierte Heizungs-Insights"""
            try:
                from src.decision_engine.heating_optimizer import HeatingOptimizer

                optimizer = HeatingOptimizer(db=self.db)
                days_back = int(request.args.get('days', 14))

                # Hole gespeicherte Insights aus DB
                insights = self.db.get_latest_heating_insights(
                    days_back=7,
                    min_confidence=0.6,
                    limit=10
                )

                # Wenn keine Insights vorhanden, generiere neue
                if not insights:
                    logger.info("No insights found in DB, generating new ones")
                    insights = optimizer.generate_insights(days_back=days_back)

                return jsonify({
                    'success': True,
                    'insights': insights,
                    'count': len(insights)
                })

            except Exception as e:
                logger.error(f"Error getting heating insights: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/heating/patterns')
        def api_heating_patterns():
            """Analysiere Heizmuster"""
            try:
                from src.decision_engine.heating_optimizer import HeatingOptimizer

                optimizer = HeatingOptimizer(db=self.db)
                days_back = int(request.args.get('days', 14))

                patterns = optimizer.analyze_patterns(days_back=days_back)

                return jsonify({
                    'success': True,
                    **patterns
                })

            except Exception as e:
                logger.error(f"Error analyzing heating patterns: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/heating/schedule')
        def api_heating_schedule():
            """Hole optimierten Heizplan"""
            try:
                from src.decision_engine.heating_optimizer import HeatingOptimizer

                optimizer = HeatingOptimizer(db=self.db)
                device_id = request.args.get('device_id')

                schedule = optimizer.get_recommended_schedule(device_id=device_id)

                return jsonify({
                    'success': True,
                    'schedule': schedule,
                    'count': len(schedule)
                })

            except Exception as e:
                logger.error(f"Error getting heating schedule: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/heating/statistics')
        def api_heating_statistics():
            """Hole Heizungs-Statistiken"""
            try:
                days_back = int(request.args.get('days', 30))
                stats = self.db.get_heating_statistics(days_back=days_back)

                return jsonify({
                    'success': True,
                    **stats
                })

            except Exception as e:
                logger.error(f"Error getting heating statistics: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/heating/collect', methods=['POST'])
        def api_heating_collect():
            """Sammle aktuellen Heizungszustand (für Optimierung)"""
            try:
                from src.decision_engine.heating_optimizer import HeatingOptimizer

                optimizer = HeatingOptimizer(db=self.db)

                # Hole Außentemperatur
                outdoor_temp = None
                if self.engine and self.engine.weather:
                    weather_data = self.engine.weather.get_weather_data(self.engine.platform)
                    if weather_data:
                        outdoor_temp = weather_data.get('temperature')

                # Sammle Daten
                result = optimizer.collect_current_state(
                    platform=self.engine.platform if self.engine else None,
                    outdoor_temp=outdoor_temp
                )

                return jsonify({
                    'success': True,
                    **result
                })

            except Exception as e:
                logger.error(f"Error collecting heating data: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/heating/analytics')
        def api_heating_analytics():
            """Hole umfassende Heizungs-Analytics"""
            try:
                days_back = int(request.args.get('days', 7))

                analytics = self._calculate_heating_analytics(days_back)

                return jsonify({
                    'success': True,
                    **analytics
                })

            except Exception as e:
                logger.error(f"Error getting heating analytics: {e}")
                return jsonify({'error': str(e)}), 500

        # ===== Analytics Endpoints =====

        @self.app.route('/api/analytics/comfort')
        def api_analytics_comfort():
            """Hole Komfort-Metriken"""
            try:
                hours_back = int(request.args.get('hours', 168))  # Default: 7 Tage

                # Hole Sensordaten
                sensor_data = self.db.get_sensor_data(hours_back=hours_back)

                # Berechne Komfort-Score
                comfort_metrics = self._calculate_comfort_metrics(sensor_data, hours_back)

                return jsonify({
                    'success': True,
                    **comfort_metrics
                })

            except Exception as e:
                logger.error(f"Error getting comfort analytics: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/analytics/ml-performance')
        def api_analytics_ml_performance():
            """Hole ML-Model Performance Metriken"""
            try:
                days_back = int(request.args.get('days', 30))

                # Hole Training History
                training_history = self._get_training_history(days_back)

                # Hole Entscheidungs-Statistiken
                decision_stats = self._get_decision_statistics(days_back)

                # Hole Confidence-Scores über Zeit
                confidence_trends = self._get_confidence_trends(days_back)

                return jsonify({
                    'success': True,
                    'training_history': training_history,
                    'decision_stats': decision_stats,
                    'confidence_trends': confidence_trends
                })

            except Exception as e:
                logger.error(f"Error getting ML performance analytics: {e}")
                return jsonify({'error': str(e)}), 500

        # ===== System Update Endpoints =====

        @self.app.route('/api/system/version')
        def get_version():
            """Hole aktuelle Git-Version"""
            try:
                # Prüfe ob Git-Repository vorhanden
                project_root = Path(__file__).parent.parent.parent
                git_dir = project_root / '.git'

                if not git_dir.exists():
                    return jsonify({
                        'success': False,
                        'error': 'Kein Git-Repository gefunden'
                    })

                # Hole aktuelle Commit-Info
                result = subprocess.run(
                    ['git', 'log', '-1', '--format=%H|%h|%s|%ar'],
                    cwd=str(project_root),
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    full_hash, short_hash, message, time_ago = result.stdout.strip().split('|', 3)

                    return jsonify({
                        'success': True,
                        'version': {
                            'commit': short_hash,
                            'commit_full': full_hash,
                            'message': message,
                            'time': time_ago
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Konnte Versions-Info nicht abrufen'
                    })

            except Exception as e:
                logger.error(f"Error getting version: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/system/check-update')
        def check_update():
            """Prüfe ob Updates verfügbar sind"""
            try:
                project_root = Path(__file__).parent.parent.parent

                # Fetch remote
                subprocess.run(
                    ['git', 'fetch', 'origin'],
                    cwd=str(project_root),
                    capture_output=True
                )

                # Prüfe wie viele Commits zurück
                result = subprocess.run(
                    ['git', 'rev-list', 'HEAD..origin/main', '--count'],
                    cwd=str(project_root),
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    commits_behind = int(result.stdout.strip())

                    if commits_behind > 0:
                        # Hole Liste der neuen Commits
                        commits_result = subprocess.run(
                            ['git', 'log', 'HEAD..origin/main', '--oneline', '--no-merges'],
                            cwd=str(project_root),
                            capture_output=True,
                            text=True
                        )

                        new_commits = []
                        if commits_result.returncode == 0:
                            for line in commits_result.stdout.strip().split('\n'):
                                if line:
                                    hash_msg = line.split(' ', 1)
                                    if len(hash_msg) == 2:
                                        new_commits.append({
                                            'hash': hash_msg[0],
                                            'message': hash_msg[1]
                                        })

                        return jsonify({
                            'success': True,
                            'update_available': True,
                            'commits_behind': commits_behind,
                            'new_commits': new_commits[:5]  # Max 5 neueste
                        })
                    else:
                        return jsonify({
                            'success': True,
                            'update_available': False,
                            'message': 'System ist auf dem neuesten Stand'
                        })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Konnte Update-Status nicht prüfen'
                    })

            except Exception as e:
                logger.error(f"Error checking for updates: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/system/update', methods=['POST'])
        def trigger_update():
            """Starte System-Update"""
            try:
                project_root = Path(__file__).parent.parent.parent
                update_script = project_root / 'update.sh'

                if not update_script.exists():
                    return jsonify({
                        'success': False,
                        'error': 'Update-Script nicht gefunden'
                    })

                # Starte Update-Script im Hintergrund
                logger.info("Starting system update...")

                # Führe Update-Script aus (läuft im Hintergrund und startet Server neu)
                subprocess.Popen(
                    ['bash', str(update_script)],
                    cwd=str(project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )

                return jsonify({
                    'success': True,
                    'message': 'Update wird durchgeführt. System startet in wenigen Sekunden neu...'
                })

            except Exception as e:
                logger.error(f"Error triggering update: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # === DATENBANK-MANAGEMENT ENDPOINTS ===

        @self.app.route('/api/database/status')
        def database_status():
            """Gibt den aktuellen Status der Datenbank zurück"""
            try:
                db_info = self.db.get_database_size()

                # Retention-Einstellung aus Config
                retention_days = self.engine.config.get('database.retention_days', 90) if self.engine else 90

                # Maintenance Job Status
                maintenance_status = {}
                if self.db_maintenance:
                    status = self.db_maintenance.get_status()
                    maintenance_status = {
                        'running': status['running'],
                        'last_cleanup': status['last_cleanup'],
                        'last_vacuum': status['last_vacuum'],
                        'retention_days': status['retention_days'],
                        'next_run_hour': status['run_hour']
                    }

                return jsonify({
                    'success': True,
                    'database': {
                        'file_size_mb': db_info['file_size_mb'],
                        'file_size_bytes': db_info['file_size_bytes'],
                        'total_rows': db_info['total_rows'],
                        'table_counts': db_info['table_counts'],
                        'oldest_data': db_info['oldest_data'],
                        'newest_data': db_info['newest_data'],
                        'file_path': db_info['file_path']
                    },
                    'settings': {
                        'retention_days': retention_days
                    },
                    'maintenance': maintenance_status
                })
            except Exception as e:
                logger.error(f"Error getting database status: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/database/cleanup', methods=['POST'])
        def database_cleanup():
            """Führt manuelles Cleanup der Datenbank aus"""
            try:
                data = request.json or {}
                retention_days = data.get('retention_days')

                # Verwende Config-Wert wenn nicht angegeben
                if retention_days is None:
                    retention_days = self.engine.config.get('database.retention_days', 90) if self.engine else 90

                deleted_counts = self.db.cleanup_old_data(retention_days=retention_days)

                return jsonify({
                    'success': True,
                    'deleted_rows': sum(deleted_counts.values()),
                    'details': deleted_counts,
                    'message': f'Cleanup abgeschlossen: {sum(deleted_counts.values())} Zeilen gelöscht'
                })
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/database/vacuum', methods=['POST'])
        def database_vacuum():
            """Führt VACUUM auf der Datenbank aus (Optimierung)"""
            try:
                # Speichere Größe vor VACUUM
                before_info = self.db.get_database_size()
                before_size = before_info['file_size_mb']

                # Führe VACUUM aus
                self.db.vacuum_database()

                # Speichere Größe nach VACUUM
                after_info = self.db.get_database_size()
                after_size = after_info['file_size_mb']

                freed_mb = before_size - after_size

                return jsonify({
                    'success': True,
                    'before_size_mb': before_size,
                    'after_size_mb': after_size,
                    'freed_mb': round(freed_mb, 2),
                    'message': f'VACUUM abgeschlossen: {round(freed_mb, 2)} MB freigegeben'
                })
            except Exception as e:
                logger.error(f"Error during vacuum: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

    def _calculate_heating_analytics(self, days_back: int) -> dict:
        """Berechnet umfassende Heizungs-Analytics"""
        from datetime import datetime, timedelta
        import statistics

        observations = self.db.get_heating_observations(days_back=days_back)

        if not observations or len(observations) < 10:
            return {
                'sufficient_data': False,
                'message': f'Nicht genug Daten (min. 10 Beobachtungen, aktuell: {len(observations) if observations else 0})',
                'observations_count': len(observations) if observations else 0
            }

        # 1. Heizzeiten-Analyse
        heating_times = self._analyze_heating_times(observations)

        # 2. Temperatur-Effizienz
        temp_efficiency = self._analyze_temperature_efficiency(observations)

        # 3. Heizkosten-Schätzung
        cost_estimates = self._estimate_heating_costs(observations, days_back)

        # 4. Raum-Vergleiche
        room_comparison = self._compare_rooms(observations)

        # 5. Wetter-Korrelation
        weather_correlation = self._analyze_weather_correlation(observations)

        return {
            'sufficient_data': True,
            'observations_count': len(observations),
            'period_days': days_back,
            'heating_times': heating_times,
            'temperature_efficiency': temp_efficiency,
            'cost_estimates': cost_estimates,
            'room_comparison': room_comparison,
            'weather_correlation': weather_correlation
        }

    def _analyze_heating_times(self, observations: list) -> dict:
        """Analysiert wann am meisten geheizt wird"""
        import statistics

        # Gruppiere nach Stunde
        hourly_heating = {}
        for obs in observations:
            hour = obs.get('hour_of_day')
            if hour is not None:
                if hour not in hourly_heating:
                    hourly_heating[hour] = {'count': 0, 'heating': 0}
                hourly_heating[hour]['count'] += 1
                if obs.get('is_heating'):
                    hourly_heating[hour]['heating'] += 1

        # Berechne Heizprozentsatz pro Stunde
        hourly_data = []
        for hour in range(24):
            if hour in hourly_heating:
                total = hourly_heating[hour]['count']
                heating = hourly_heating[hour]['heating']
                percentage = (heating / total * 100) if total > 0 else 0
                hourly_data.append({
                    'hour': hour,
                    'heating_percentage': round(percentage, 1),
                    'observations': total
                })
            else:
                hourly_data.append({
                    'hour': hour,
                    'heating_percentage': 0,
                    'observations': 0
                })

        # Peak Heizzeiten
        sorted_hours = sorted(hourly_data, key=lambda x: x['heating_percentage'], reverse=True)
        peak_hours = sorted_hours[:5]

        return {
            'hourly_data': hourly_data,
            'peak_hours': peak_hours
        }

    def _analyze_temperature_efficiency(self, observations: list) -> dict:
        """Analysiert Temperatur-Effizienz (Soll vs. Ist)"""
        import statistics

        deviations = []
        for obs in observations:
            target = obs.get('target_temperature')
            current = obs.get('current_temperature')
            if target and current:
                deviation = abs(target - current)
                deviations.append({
                    'target': target,
                    'current': current,
                    'deviation': deviation,
                    'timestamp': obs.get('timestamp')
                })

        if not deviations:
            return {'available': False}

        deviation_values = [d['deviation'] for d in deviations]

        # Effizienz-Score (0-100, je geringer die Abweichung, desto besser)
        avg_deviation = statistics.mean(deviation_values)
        # 0°C Abweichung = 100%, 2°C = 0%
        efficiency_score = max(0, 100 - (avg_deviation / 2.0 * 100))

        return {
            'available': True,
            'avg_deviation': round(avg_deviation, 2),
            'min_deviation': round(min(deviation_values), 2),
            'max_deviation': round(max(deviation_values), 2),
            'efficiency_score': round(efficiency_score, 1),
            'samples': len(deviations)
        }

    def _estimate_heating_costs(self, observations: list, days: int) -> dict:
        """Schätzt Heizkosten"""
        import statistics

        # Zähle Heizstunden
        heating_count = sum(1 for obs in observations if obs.get('is_heating'))
        total_count = len(observations)

        # Annahme: Alle 15 Minuten eine Beobachtung
        minutes_per_observation = 15
        total_minutes = total_count * minutes_per_observation
        heating_minutes = heating_count * minutes_per_observation
        heating_hours = heating_minutes / 60

        # Kosten-Schätzungen (grobe Annahmen)
        # Gas: ~0.15€/kWh, Durchschnitt-Heizung: 10-15 kW
        avg_heating_power_kw = 12  # kW
        cost_per_kwh = 0.15  # EUR

        # Tagesverbrauch
        hours_per_day = total_minutes / days / 60
        heating_hours_per_day = heating_minutes / days / 60
        daily_kwh = heating_hours_per_day * avg_heating_power_kw
        daily_cost = daily_kwh * cost_per_kwh

        # Wochenverbrauch
        weekly_cost = daily_cost * 7

        # Monatsverbrauch
        monthly_cost = daily_cost * 30

        # Hochrechnung Jahresverbrauch
        yearly_cost = daily_cost * 365

        return {
            'heating_hours_total': round(heating_hours, 1),
            'heating_hours_per_day': round(heating_hours_per_day, 1),
            'heating_percentage': round((heating_count / total_count * 100), 1) if total_count > 0 else 0,
            'costs': {
                'daily': round(daily_cost, 2),
                'weekly': round(weekly_cost, 2),
                'monthly': round(monthly_cost, 2),
                'yearly': round(yearly_cost, 2)
            },
            'consumption': {
                'daily_kwh': round(daily_kwh, 1),
                'monthly_kwh': round(daily_kwh * 30, 1),
                'yearly_kwh': round(daily_kwh * 365, 0)
            },
            'assumptions': {
                'avg_power_kw': avg_heating_power_kw,
                'cost_per_kwh': cost_per_kwh,
                'observation_interval_min': minutes_per_observation
            }
        }

    def _compare_rooms(self, observations: list) -> dict:
        """Vergleicht Heizverhalten zwischen Räumen"""
        import statistics

        rooms = {}
        for obs in observations:
            room = obs.get('room_name', 'Unbekannt')
            if room not in rooms:
                rooms[room] = {
                    'observations': 0,
                    'heating_count': 0,
                    'temps': [],
                    'target_temps': []
                }

            rooms[room]['observations'] += 1
            if obs.get('is_heating'):
                rooms[room]['heating_count'] += 1

            if obs.get('current_temperature'):
                rooms[room]['temps'].append(obs['current_temperature'])
            if obs.get('target_temperature'):
                rooms[room]['target_temps'].append(obs['target_temperature'])

        # Berechne Statistiken pro Raum
        room_stats = []
        for room, data in rooms.items():
            heating_pct = (data['heating_count'] / data['observations'] * 100) if data['observations'] > 0 else 0
            avg_temp = statistics.mean(data['temps']) if data['temps'] else None
            avg_target = statistics.mean(data['target_temps']) if data['target_temps'] else None

            room_stats.append({
                'room': room,
                'observations': data['observations'],
                'heating_percentage': round(heating_pct, 1),
                'avg_temperature': round(avg_temp, 1) if avg_temp else None,
                'avg_target_temperature': round(avg_target, 1) if avg_target else None
            })

        # Sortiere nach Heizprozentsatz
        room_stats.sort(key=lambda x: x['heating_percentage'], reverse=True)

        return {
            'rooms': room_stats,
            'room_count': len(room_stats)
        }

    def _analyze_weather_correlation(self, observations: list) -> dict:
        """Analysiert Korrelation zwischen Außentemperatur und Heizverhalten"""
        import statistics

        # Gruppiere nach Außentemperatur-Bereichen
        temp_ranges = {
            'below_0': {'heating': 0, 'total': 0, 'label': 'Unter 0°C'},
            '0_to_5': {'heating': 0, 'total': 0, 'label': '0-5°C'},
            '5_to_10': {'heating': 0, 'total': 0, 'label': '5-10°C'},
            '10_to_15': {'heating': 0, 'total': 0, 'label': '10-15°C'},
            'above_15': {'heating': 0, 'total': 0, 'label': 'Über 15°C'}
        }

        outdoor_temps = []

        for obs in observations:
            outdoor_temp = obs.get('outdoor_temperature')
            if outdoor_temp is None:
                continue

            outdoor_temps.append(outdoor_temp)

            # Bestimme Range
            if outdoor_temp < 0:
                range_key = 'below_0'
            elif outdoor_temp < 5:
                range_key = '0_to_5'
            elif outdoor_temp < 10:
                range_key = '5_to_10'
            elif outdoor_temp < 15:
                range_key = '10_to_15'
            else:
                range_key = 'above_15'

            temp_ranges[range_key]['total'] += 1
            if obs.get('is_heating'):
                temp_ranges[range_key]['heating'] += 1

        # Berechne Heizprozentsatz pro Range
        correlation_data = []
        for key, data in temp_ranges.items():
            if data['total'] > 0:
                heating_pct = (data['heating'] / data['total'] * 100)
                correlation_data.append({
                    'range': data['label'],
                    'heating_percentage': round(heating_pct, 1),
                    'observations': data['total']
                })

        # Durchschnittliche Außentemperatur
        avg_outdoor = statistics.mean(outdoor_temps) if outdoor_temps else None

        return {
            'available': len(outdoor_temps) > 0,
            'correlation_data': correlation_data,
            'avg_outdoor_temp': round(avg_outdoor, 1) if avg_outdoor else None,
            'samples_with_weather': len(outdoor_temps)
        }

    def _calculate_comfort_metrics(self, sensor_data: list, hours_back: int) -> dict:
        """Berechnet Komfort-Metriken aus Sensordaten"""
        from datetime import datetime, timedelta
        import statistics

        # Gruppiere nach Sensor-Typ
        temps = [s for s in sensor_data if s['sensor_type'] == 'temperature']
        humids = [s for s in sensor_data if s['sensor_type'] == 'humidity']
        motion = [s for s in sensor_data if s['sensor_type'] == 'motion']

        # Komfort-Score berechnen (0-100)
        comfort_score = 0
        comfort_details = []

        if temps:
            temp_values = [t['value'] for t in temps if t['value']]
            avg_temp = statistics.mean(temp_values) if temp_values else 20.0

            # Ideal: 20-22°C
            if 20 <= avg_temp <= 22:
                temp_score = 100
                comfort_details.append("Temperatur ideal")
            elif 18 <= avg_temp < 20 or 22 < avg_temp <= 24:
                temp_score = 75
                comfort_details.append("Temperatur gut")
            elif 16 <= avg_temp < 18 or 24 < avg_temp <= 26:
                temp_score = 50
                comfort_details.append("Temperatur akzeptabel")
            else:
                temp_score = 25
                comfort_details.append("Temperatur suboptimal")

            comfort_score += temp_score * 0.5  # 50% Gewichtung
        else:
            avg_temp = None

        if humids:
            humid_values = [h['value'] for h in humids if h['value']]
            avg_humid = statistics.mean(humid_values) if humid_values else 50.0

            # Ideal: 40-60%
            if 40 <= avg_humid <= 60:
                humid_score = 100
                comfort_details.append("Luftfeuchtigkeit ideal")
            elif 30 <= avg_humid < 40 or 60 < avg_humid <= 70:
                humid_score = 75
                comfort_details.append("Luftfeuchtigkeit gut")
            else:
                humid_score = 50
                comfort_details.append("Luftfeuchtigkeit suboptimal")

            comfort_score += humid_score * 0.5  # 50% Gewichtung
        else:
            avg_humid = None

        # Anwesenheits-Muster
        presence_pattern = []
        if motion:
            # Gruppiere nach Stunden
            now = datetime.now()
            for hour in range(24):
                hour_start = now - timedelta(hours=hours_back - hour)
                hour_motion = [m for m in motion if
                             datetime.fromisoformat(m['timestamp']).hour == hour_start.hour]
                presence_pattern.append({
                    'hour': hour,
                    'activity': len(hour_motion)
                })

        # Schlafqualität-Indikator (Nachttemperaturen 22-6 Uhr)
        night_temps = []
        if temps:
            for t in temps:
                ts = datetime.fromisoformat(t['timestamp'])
                if 22 <= ts.hour or ts.hour < 6:
                    if t['value']:
                        night_temps.append(t['value'])

        sleep_quality = None
        if night_temps:
            avg_night_temp = statistics.mean(night_temps)
            # Ideal für Schlaf: 16-19°C
            if 16 <= avg_night_temp <= 19:
                sleep_quality = {
                    'score': 100,
                    'avg_temp': round(avg_night_temp, 1),
                    'rating': 'Ideal',
                    'description': 'Optimale Temperatur für erholsamen Schlaf'
                }
            elif 14 <= avg_night_temp < 16 or 19 < avg_night_temp <= 21:
                sleep_quality = {
                    'score': 75,
                    'avg_temp': round(avg_night_temp, 1),
                    'rating': 'Gut',
                    'description': 'Temperatur leicht außerhalb des optimalen Bereichs'
                }
            else:
                sleep_quality = {
                    'score': 50,
                    'avg_temp': round(avg_night_temp, 1),
                    'rating': 'Verbesserungswürdig',
                    'description': 'Temperatur könnte Schlafqualität beeinträchtigen'
                }

        return {
            'comfort_score': round(comfort_score, 1),
            'comfort_details': comfort_details,
            'avg_temperature': round(avg_temp, 1) if avg_temp else None,
            'avg_humidity': round(avg_humid, 1) if avg_humid else None,
            'presence_pattern': presence_pattern[:24],  # Nur letzte 24h
            'sleep_quality': sleep_quality,
            'period_hours': hours_back
        }

    def _get_training_history(self, days_back: int) -> list:
        """Holt Training History der ML-Modelle"""
        from datetime import datetime, timedelta

        conn = self.db._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(days=days_back)

        cursor.execute("""
            SELECT timestamp, model_name, model_type, metrics
            FROM training_history
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 50
        """, (start_time,))

        history = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            # Parse metrics JSON
            if row_dict.get('metrics'):
                try:
                    row_dict['metrics'] = json.loads(row_dict['metrics'])
                except:
                    pass
            history.append(row_dict)

        return history

    def _get_decision_statistics(self, days_back: int) -> dict:
        """Berechnet Statistiken über KI-Entscheidungen"""
        from datetime import datetime, timedelta

        conn = self.db._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(days=days_back)

        # Gesamt-Statistiken
        cursor.execute("""
            SELECT
                COUNT(*) as total_decisions,
                SUM(CASE WHEN executed = 1 THEN 1 ELSE 0 END) as executed_decisions,
                AVG(confidence) as avg_confidence,
                decision_type,
                COUNT(*) as count_per_type
            FROM decisions
            WHERE timestamp >= ?
            GROUP BY decision_type
        """, (start_time,))

        type_stats = []
        total_decisions = 0
        executed_decisions = 0

        for row in cursor.fetchall():
            row_dict = dict(row)
            type_stats.append(row_dict)
            total_decisions += row_dict['count_per_type']
            executed_decisions += row_dict.get('executed_decisions', 0)

        # Durchschnittliche Confidence
        cursor.execute("""
            SELECT AVG(confidence) as avg_confidence
            FROM decisions
            WHERE timestamp >= ?
        """, (start_time,))

        result = cursor.fetchone()
        avg_confidence = result['avg_confidence'] if result else 0.0

        return {
            'total_decisions': total_decisions,
            'executed_decisions': executed_decisions,
            'execution_rate': round((executed_decisions / total_decisions * 100), 1) if total_decisions > 0 else 0,
            'avg_confidence': round(avg_confidence, 3) if avg_confidence else 0,
            'by_type': type_stats,
            'period_days': days_back
        }

    def _get_confidence_trends(self, days_back: int) -> list:
        """Holt Confidence-Score Trends über Zeit"""
        from datetime import datetime, timedelta

        conn = self.db._get_connection()
        cursor = conn.cursor()

        start_time = datetime.now() - timedelta(days=days_back)

        cursor.execute("""
            SELECT
                DATE(timestamp) as date,
                AVG(confidence) as avg_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence,
                COUNT(*) as decision_count
            FROM decisions
            WHERE timestamp >= ? AND confidence IS NOT NULL
            GROUP BY DATE(timestamp)
            ORDER BY date ASC
        """, (start_time,))

        trends = []
        for row in cursor.fetchall():
            trends.append({
                'date': row['date'],
                'avg_confidence': round(row['avg_confidence'], 3),
                'min_confidence': round(row['min_confidence'], 3),
                'max_confidence': round(row['max_confidence'], 3),
                'decision_count': row['decision_count']
            })

        return trends

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Starte den Web-Server"""
        logger.info(f"Starting web interface on http://{host}:{port}")

        # Starte Background Data Collector
        if self.background_collector:
            self.background_collector.start()
            logger.info("Background Data Collector started")

        # Starte ML Auto-Trainer
        if self.ml_auto_trainer:
            self.ml_auto_trainer.start()
            logger.info("ML Auto-Trainer started (runs daily at 2:00)")

        # Starte Bathroom Optimizer
        if self.bathroom_optimizer:
            self.bathroom_optimizer.start()
            logger.info("Bathroom Optimizer started (runs daily at 3:00)")

        # Starte Heating Data Collector
        if self.heating_collector:
            self.heating_collector.start()
            logger.info("Heating Data Collector started (collects every 15min, optimizes daily at 4:00)")

        # Starte Bathroom Data Collector
        if self.bathroom_collector:
            self.bathroom_collector.start()
            logger.info("Bathroom Data Collector started (collects every 60s)")

        # Starte Database Maintenance Job
        if self.db_maintenance:
            self.db_maintenance.start()
            logger.info("Database Maintenance Job started (runs daily at 5:00)")

        try:
            self.app.run(host=host, port=port, debug=debug)
        finally:
            # Stoppe Background Processes beim Herunterfahren
            if self.background_collector:
                self.background_collector.stop()
                logger.info("Background Data Collector stopped")

            if self.ml_auto_trainer:
                self.ml_auto_trainer.stop()
                logger.info("ML Auto-Trainer stopped")

            if self.bathroom_optimizer:
                self.bathroom_optimizer.stop()
                logger.info("Bathroom Optimizer stopped")

            if self.heating_collector:
                self.heating_collector.stop()
                logger.info("Heating Data Collector stopped")

            if self.bathroom_collector:
                self.bathroom_collector.stop()
                logger.info("Bathroom Data Collector stopped")

            if self.db_maintenance:
                self.db_maintenance.stop()
                logger.info("Database Maintenance Job stopped")


def create_app(config_path=None):
    """Factory-Funktion für Flask App"""
    web = WebInterface(config_path)
    return web.app
