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

# Füge src zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.decision_engine.engine import DecisionEngine
from src.data_collector.background_collector import BackgroundDataCollector
from src.background.bathroom_optimizer import BathroomOptimizer
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

        # Registriere Routen
        self._register_routes()

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

        @self.app.route('/rooms')
        def rooms_page():
            """Räume & Zonen Seite"""
            return render_template('rooms.html')

        @self.app.route('/analytics')
        def analytics_page():
            """Analytics & Verlaufs-Statistiken Seite"""
            return render_template('analytics.html')

        @self.app.route('/bathroom')
        def bathroom_page():
            """Badezimmer Automatisierung Seite"""
            return render_template('bathroom.html')

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
                            devices.append({
                                'id': entity_id,
                                'name': state_data.get('attributes', {}).get('friendly_name', entity_id),
                                'domain': domain,
                                'state': state_data.get('state'),
                                'attributes': state_data.get('attributes', {}),
                                'last_updated': state_data.get('last_updated')
                            })
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

                # Simuliere Vorhersagen (würde normalerweise vom ML-Modell kommen)
                state = self.engine.collect_current_state()

                predictions = {
                    'lighting': {
                        'suggested_actions': recommendations.get('lighting', recommendations.get('general', [])),
                        'confidence': 0.85,
                        'reasoning': 'Basierend auf Tageszeit, Helligkeit und bisherigem Verhalten'
                    },
                    'heating': {
                        'suggested_actions': recommendations.get('heating', []),
                        'confidence': 0.78,
                        'reasoning': 'Basierend auf Außentemperatur, Energiepreis und Komfort-Präferenzen'
                    },
                    'energy': {
                        'optimization': 'Niedrige Energiepreise - guter Zeitpunkt für Heizen',
                        'savings_potential': '15%',
                        'confidence': 0.72
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

        @self.app.route('/api/bathroom/config', methods=['GET', 'POST'])
        def api_bathroom_config():
            """API: Badezimmer-Konfiguration verwalten"""
            import json
            from pathlib import Path

            config_file = Path('data/bathroom_config.json')

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

        @self.app.route('/api/bathroom/status')
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

                config_file = Path('data/bathroom_config.json')

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

        @self.app.route('/api/bathroom/test', methods=['POST'])
        def api_bathroom_test():
            """API: Badezimmer-Automatisierung testen"""
            try:
                import json
                from pathlib import Path
                from src.decision_engine.bathroom_automation import BathroomAutomation

                config_file = Path('data/bathroom_config.json')

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

        @self.app.route('/api/bathroom/analytics')
        def api_bathroom_analytics():
            """API: Badezimmer Analytics und Statistiken"""
            try:
                import json
                from pathlib import Path
                from src.decision_engine.bathroom_automation import BathroomAutomation

                config_file = Path('data/bathroom_config.json')

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

        @self.app.route('/api/bathroom/events')
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

        @self.app.route('/api/bathroom/optimize', methods=['POST'])
        def api_bathroom_optimize():
            """API: Badezimmer Parameter optimieren"""
            try:
                import json
                from pathlib import Path
                from src.decision_engine.bathroom_automation import BathroomAutomation

                config_file = Path('data/bathroom_config.json')

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

        @self.app.route('/bathroom/analytics')
        def page_bathroom_analytics():
            """Seite: Badezimmer Analytics Dashboard"""
            return render_template('bathroom_analytics.html')

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Starte den Web-Server"""
        logger.info(f"Starting web interface on http://{host}:{port}")

        # Starte Background Data Collector
        if self.background_collector:
            self.background_collector.start()
            logger.info("Background Data Collector started")

        # Starte Bathroom Optimizer
        if self.bathroom_optimizer:
            self.bathroom_optimizer.start()
            logger.info("Bathroom Optimizer started (runs daily at 3:00)")

        try:
            self.app.run(host=host, port=port, debug=debug)
        finally:
            # Stoppe Background Processes beim Herunterfahren
            if self.background_collector:
                self.background_collector.stop()
                logger.info("Background Data Collector stopped")

            if self.bathroom_optimizer:
                self.bathroom_optimizer.stop()
                logger.info("Bathroom Optimizer stopped")


def create_app(config_path=None):
    """Factory-Funktion für Flask App"""
    web = WebInterface(config_path)
    return web.app
