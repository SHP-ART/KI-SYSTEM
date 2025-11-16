"""
Model Version Manager
Verwaltet ML-Model Versionen, Rollback und Performance-Monitoring
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from loguru import logger


class ModelVersionManager:
    """
    Verwaltet Versionierung von ML-Modellen

    Features:
    - Automatisches Backup vor Training
    - Version History
    - Performance-Vergleich
    - Rollback zu vorheriger Version
    - Model Registry (Metadaten)
    """

    def __init__(self, models_dir: str = 'models'):
        """
        Args:
            models_dir: Basis-Verzeichnis für Modelle
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        # Versions-Verzeichnis
        self.versions_dir = self.models_dir / 'versions'
        self.versions_dir.mkdir(exist_ok=True)

        # Registry-Datei (JSON)
        self.registry_file = self.models_dir / 'model_registry.json'
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict:
        """Lädt Model Registry aus JSON"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading registry: {e}")
                return {}
        return {}

    def _save_registry(self):
        """Speichert Model Registry als JSON"""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving registry: {e}")

    def backup_current_model(self, model_name: str) -> Optional[str]:
        """
        Erstellt Backup des aktuellen Modells

        Args:
            model_name: Name des Modells (z.B. 'lighting_model', 'temperature_model')

        Returns:
            Pfad zum Backup oder None
        """
        model_path = self.models_dir / f"{model_name}.pkl"

        if not model_path.exists():
            logger.warning(f"No current model found to backup: {model_name}")
            return None

        # Erstelle Backup mit Timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{model_name}_{timestamp}.pkl"
        backup_path = self.versions_dir / backup_filename

        try:
            shutil.copy2(model_path, backup_path)
            logger.info(f"Backed up model: {model_name} -> {backup_filename}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Error backing up model: {e}")
            return None

    def register_model(self, model_name: str, metrics: Dict,
                      version: str = None, notes: str = None) -> bool:
        """
        Registriert ein neues Modell mit Metadaten

        Args:
            model_name: Name des Modells
            metrics: Performance-Metriken (accuracy, mae, r2, etc.)
            version: Version String (default: Timestamp)
            notes: Optionale Notizen

        Returns:
            True bei Erfolg
        """
        if version is None:
            version = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Erstelle Registry-Eintrag
        if model_name not in self.registry:
            self.registry[model_name] = {
                'current_version': version,
                'versions': []
            }

        # Füge Version hinzu
        version_entry = {
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'notes': notes,
            'model_path': f"{model_name}.pkl"
        }

        self.registry[model_name]['versions'].append(version_entry)
        self.registry[model_name]['current_version'] = version

        # Behalte nur letzte 10 Versionen in Registry
        if len(self.registry[model_name]['versions']) > 10:
            self.registry[model_name]['versions'] = self.registry[model_name]['versions'][-10:]

        self._save_registry()
        logger.info(f"Registered model version: {model_name} v{version}")
        return True

    def compare_with_previous(self, model_name: str, new_metrics: Dict) -> Dict:
        """
        Vergleicht neue Metriken mit vorheriger Version

        Args:
            model_name: Name des Modells
            new_metrics: Neue Performance-Metriken

        Returns:
            Dict mit Vergleich:
            {
                'improved': bool,
                'previous_metrics': dict,
                'new_metrics': dict,
                'differences': dict,
                'recommendation': str
            }
        """
        if model_name not in self.registry:
            return {
                'improved': True,  # Keine Vorgänger-Version
                'previous_metrics': None,
                'new_metrics': new_metrics,
                'differences': {},
                'recommendation': 'Erste Version - Akzeptieren'
            }

        versions = self.registry[model_name]['versions']
        if len(versions) < 1:
            return {
                'improved': True,
                'previous_metrics': None,
                'new_metrics': new_metrics,
                'differences': {},
                'recommendation': 'Keine Vorgänger-Metriken - Akzeptieren'
            }

        # Hole letzte Version
        previous_version = versions[-1]
        previous_metrics = previous_version['metrics']

        # Berechne Unterschiede
        differences = {}
        improved_count = 0
        worse_count = 0

        # Für Classification (Lighting)
        if 'accuracy' in new_metrics and 'accuracy' in previous_metrics:
            diff = new_metrics['accuracy'] - previous_metrics['accuracy']
            differences['accuracy'] = diff
            if diff > 0.01:  # >1% Verbesserung
                improved_count += 1
            elif diff < -0.01:  # >1% Verschlechterung
                worse_count += 1

        # Für Regression (Temperature)
        if 'mae' in new_metrics and 'mae' in previous_metrics:
            diff = previous_metrics['mae'] - new_metrics['mae']  # Niedriger MAE ist besser
            differences['mae'] = diff
            if diff > 0.1:  # >0.1°C Verbesserung
                improved_count += 1
            elif diff < -0.1:  # >0.1°C Verschlechterung
                worse_count += 1

        if 'r2_score' in new_metrics and 'r2_score' in previous_metrics:
            diff = new_metrics['r2_score'] - previous_metrics['r2_score']
            differences['r2_score'] = diff
            if diff > 0.02:  # >2% Verbesserung
                improved_count += 1
            elif diff < -0.02:  # >2% Verschlechterung
                worse_count += 1

        # Bewertung
        if improved_count > worse_count:
            improved = True
            recommendation = f"✅ Verbesserung erkannt ({improved_count} Metriken besser) - Akzeptieren"
        elif worse_count > improved_count:
            improved = False
            recommendation = f"⚠️ Verschlechterung erkannt ({worse_count} Metriken schlechter) - Eventuell Rollback"
        else:
            improved = True  # Bei Gleichstand: akzeptieren
            recommendation = "➡️ Keine signifikante Änderung - Akzeptieren"

        return {
            'improved': improved,
            'previous_metrics': previous_metrics,
            'new_metrics': new_metrics,
            'differences': differences,
            'recommendation': recommendation,
            'improved_metrics': improved_count,
            'worse_metrics': worse_count
        }

    def rollback_to_previous(self, model_name: str) -> bool:
        """
        Rollback zu vorheriger Model-Version

        Args:
            model_name: Name des Modells

        Returns:
            True bei Erfolg
        """
        if model_name not in self.registry:
            logger.error(f"No registry entry for {model_name}")
            return False

        versions = self.registry[model_name]['versions']
        if len(versions) < 2:
            logger.error(f"No previous version available for {model_name}")
            return False

        # Finde vorletzte Version
        previous_version = versions[-2]
        previous_timestamp = previous_version['version']

        # Suche Backup-Datei
        backup_filename = f"{model_name}_{previous_timestamp}.pkl"
        backup_path = self.versions_dir / backup_filename

        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_filename}")
            return False

        # Kopiere Backup zurück
        current_model_path = self.models_dir / f"{model_name}.pkl"
        try:
            shutil.copy2(backup_path, current_model_path)

            # Update Registry
            self.registry[model_name]['current_version'] = previous_timestamp

            # Entferne neueste Version aus Registry
            self.registry[model_name]['versions'].pop()

            self._save_registry()

            logger.info(f"✅ Rolled back {model_name} to version {previous_timestamp}")
            return True

        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return False

    def get_version_history(self, model_name: str, limit: int = 10) -> List[Dict]:
        """
        Holt Version History eines Modells

        Args:
            model_name: Name des Modells
            limit: Maximale Anzahl Versionen

        Returns:
            Liste von Version-Einträgen
        """
        if model_name not in self.registry:
            return []

        versions = self.registry[model_name]['versions']
        return versions[-limit:]

    def cleanup_old_versions(self, model_name: str, keep_last_n: int = 5):
        """
        Löscht alte Model-Versionen (Backups)

        Args:
            model_name: Name des Modells
            keep_last_n: Wie viele Versionen behalten
        """
        # Finde alle Backup-Dateien für dieses Modell
        pattern = f"{model_name}_*.pkl"
        backup_files = sorted(self.versions_dir.glob(pattern))

        # Behalte nur die neuesten N
        files_to_delete = backup_files[:-keep_last_n] if len(backup_files) > keep_last_n else []

        deleted_count = 0
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                deleted_count += 1
                logger.debug(f"Deleted old version: {file_path.name}")
            except Exception as e:
                logger.error(f"Error deleting {file_path}: {e}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old versions of {model_name}")

    def get_current_metrics(self, model_name: str) -> Optional[Dict]:
        """
        Holt Metriken der aktuellen Model-Version

        Args:
            model_name: Name des Modells

        Returns:
            Metriken-Dict oder None
        """
        if model_name not in self.registry:
            return None

        versions = self.registry[model_name]['versions']
        if len(versions) < 1:
            return None

        return versions[-1]['metrics']

    def get_summary(self) -> Dict:
        """
        Holt Zusammenfassung aller Modelle

        Returns:
            Dict mit Model-Übersicht
        """
        summary = {}

        for model_name, model_data in self.registry.items():
            current_version = model_data.get('current_version')
            versions_count = len(model_data.get('versions', []))

            current_metrics = None
            if versions_count > 0:
                current_metrics = model_data['versions'][-1]['metrics']

            summary[model_name] = {
                'current_version': current_version,
                'versions_count': versions_count,
                'current_metrics': current_metrics
            }

        return summary
