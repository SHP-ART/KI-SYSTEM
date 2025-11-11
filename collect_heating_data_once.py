#!/usr/bin/env python3
"""
Einmaliges Sammeln von Heizungsdaten
"""
import sys
sys.path.insert(0, '/Users/shp-art/Documents/Github/KI-SYSTEM')

from src.background.heating_data_collector import HeatingDataCollector
from src.decision_engine.engine import DecisionEngine
from loguru import logger

# Initialisiere Engine (für Platform-Zugriff)
engine = DecisionEngine('config/config.yaml')

# Initialisiere Collector
collector = HeatingDataCollector(engine=engine)

# Sammle einmalig Daten
logger.info("Collecting heating data once...")
collector._collect_data()
logger.info("Done!")

# Check ob Daten gesammelt wurden
from src.utils.database import Database
db = Database()
stats = db.get_heating_statistics(days_back=1)
logger.info(f"Total observations in last 24h: {stats['heating']['total_observations']}")
