# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KI-SYSTEM is an AI-powered smart home automation system written in Python that learns from user behavior to control lighting, heating, and other smart home devices. It supports both Home Assistant and Homey Pro platforms and uses machine learning models (scikit-learn) to make intelligent decisions.

**Key Design Philosophy:**
- Multi-platform support via a factory pattern (Home Assistant OR Homey Pro)
- ML models learn from sensor data to optimize energy usage and comfort
- Safety-first approach with configurable rules and thresholds
- Three operational modes: `auto` (executes actions), `learning` (collects data only), `manual` (suggests actions)

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Testing and Validation
```bash
# Quick validation of all components (preferred for rapid testing)
./quick_test.sh

# Full database test
python3 test_database.py

# Test platform connections (requires configured .env)
python3 main.py test

# View current system status
python3 main.py status
```

### Running the System
```bash
# Single cycle execution (collect data + make decisions)
python3 main.py run

# Daemon mode - continuous operation with interval
python3 main.py daemon --interval 300  # Every 5 minutes

# Train ML models manually
python3 main.py train

# Start web interface
python3 main.py web --host 0.0.0.0 --port 5000
```

### Configuration
- **Environment variables**: `.env` file (copy from `.env.example`)
- **Main config**: `config/config.yaml` - platform selection, sensors, ML model settings, decision rules
- **Platform selection**: Set `platform.type` to either `"homeassistant"` or `"homey"` in config.yaml

## Architecture

### Core Components

**Decision Engine** (`src/decision_engine/engine.py`)
- Orchestrates all system components
- Manages the decision-making cycle: collect state → run models → execute actions
- Enforces safety rules and confidence thresholds
- Entry point for all main.py commands

**Platform Abstraction Layer** (`src/data_collector/`)
- `platform_factory.py`: Factory pattern to create the correct collector (HA or Homey)
- `base_collector.py`: Abstract base class defining the SmartHomeCollector interface
- `ha_collector.py`: Home Assistant REST API implementation
- `homey_collector.py`: Homey Pro API implementation
- All collectors implement: `get_sensor_data()`, `set_light()`, `set_temperature()`, `test_connection()`

**ML Models** (`src/models/`)
- `lighting_model.py`: Predicts when lights should be on/off based on brightness, motion, time
- `temperature_model.py`: Predicts optimal heating settings based on outdoor temp, presence, energy prices
- `energy_optimizer.py`: Optimizes energy consumption vs comfort using configured constraints
- Models use scikit-learn (RandomForest/GradientBoosting) and are saved/loaded from `models/` directory

**Data Collectors** (`src/data_collector/`)
- `weather_collector.py`: Fetches weather data (OpenWeatherMap)
- `energy_price_collector.py`: Fetches dynamic energy pricing (aWATTar, Tibber)
- All data gets stored in SQLite database for training

**Database** (`src/utils/database.py`)
- SQLite-based storage for sensor data, decisions, and training history
- Schema includes: sensor_data, external_data, decisions, training_history
- Bathroom automation tables: bathroom_events, bathroom_measurements, bathroom_device_actions, bathroom_learned_parameters
- 90-day retention policy (configurable)

**Web Interface** (`src/web/app.py`)
- Flask-based dashboard with templates in `src/web/templates/`
- Real-time status, historical charts, manual control interface
- Bathroom automation dashboard with analytics and self-learning optimization

**Background Processes** (`src/background/`)
- `data_collector.py`: Automated sensor data collection every 5 minutes
- `bathroom_optimizer.py`: Daily optimization of bathroom automation thresholds (runs at 3:00 AM)

### Data Flow

1. **Collection Cycle**: DecisionEngine.run_cycle() is called (manually, daemon, or web)
2. **Gather State**: Collect sensor data from platform + weather + energy prices
3. **Store Data**: Save to database for future training
4. **ML Prediction**: Feed current state to lighting_model and temperature_model
5. **Optimization**: EnergyOptimizer balances predictions against cost/comfort constraints
6. **Safety Check**: Validate against configured rules (e.g., no heating with open windows)
7. **Execution**: If mode is "auto" and confidence > threshold, execute actions via platform
8. **Logging**: All decisions logged to database and logs/ki_system.log

### Key Patterns

**Factory Pattern for Platforms**: PlatformFactory.create_collector() returns the appropriate SmartHomeCollector subclass based on config. This allows seamless switching between Home Assistant and Homey Pro.

**Configuration Cascading**: ConfigLoader (src/utils/config_loader.py) loads config/config.yaml, merges with .env variables, provides dot-notation access: `config.get('platform.type')`

**Safety Mechanisms**:
- Confidence thresholds (default 0.7) prevent low-confidence actions
- Temperature constraints (min/max bounds)
- Configurable safety rules in decision_engine.rules array
- Learning mode for safe data collection without automation

## Important Notes

**Platform Integration:**
- System can use EITHER Home Assistant OR Homey Pro (configured via platform.type)
- Platform URLs and tokens come from .env file
- Both platforms use the same SmartHomeCollector interface, so decision logic is platform-agnostic

**ML Model Training:**
- Models require minimum samples: 100 for lighting, 200 for heating
- Auto-retraining happens every 24 hours (configurable)
- Initial deployment should run in "learning" mode for 2-3 days
- Models saved to models/ directory as .pkl files

**Energy Price Integration:**
- Optional feature (external_data.energy_prices.enabled in config)
- Disabled by default to avoid external API dependencies
- When enabled, influences heating decisions via EnergyOptimizer

**Logging:**
- Uses loguru for structured logging
- Console and file logging (logs/ki_system.log)
- Rotation at 10MB, 7-day retention
- Log level configurable in config.yaml

**Database Schema:**
- sensor_data: timestamp, sensor_type, value, metadata (JSON)
- external_data: timestamp, data_type, data (JSON)
- decisions: timestamp, decision_type, input_data, output_decision, confidence, executed, result
- training_history: timestamp, model_type, metrics (JSON)
- bathroom_events: comprehensive tracking of shower/bath events with humidity, temperature, duration
- bathroom_measurements: detailed measurements during bathroom events
- bathroom_device_actions: log of all device actions (dehumidifier, fan, etc.)
- bathroom_learned_parameters: stores optimized thresholds learned from historical data

## Testing Strategy

**Quick Test**: Run `./quick_test.sh` for rapid validation of environment, dependencies, imports, and database functionality.

**Integration Test**: Run `python3 main.py test` to verify live connections to configured platform, weather API, and database.

**Manual Testing**: Use `python3 main.py status` to inspect current system state and recommendations without executing actions.

**Safe Deployment**: Always start with `mode: "learning"` in config.yaml to collect data without automation, then switch to "manual" for approval-based automation, finally "auto" for full automation.

## Common Development Workflows

**Adding a New Sensor Type:**
1. Update config.yaml data_collection.sensors with new sensor entity IDs
2. Modify platform collector's get_sensor_data() to handle new sensor type
3. Update ML model's prepare_training_data() to include new features
4. Retrain model with python3 main.py train

**Supporting a New Platform:**
1. Create new collector in src/data_collector/ inheriting from SmartHomeCollector
2. Implement all abstract methods (get_sensor_data, set_light, set_temperature, etc.)
3. Register in PlatformFactory.PLATFORMS dictionary
4. Add configuration section to config.yaml
5. Update documentation

**Modifying Decision Logic:**
1. Decision rules are in config.yaml under decision_engine.rules
2. Custom logic should be added to DecisionEngine.run_cycle()
3. Safety checks happen in _apply_safety_checks() method
4. Confidence thresholds applied before execution

**Debugging Platform Connection Issues:**
1. Check .env file has correct PLATFORM_TYPE, URL, and TOKEN
2. Run python3 main.py test to diagnose connection
3. For Home Assistant: verify long-lived access token hasn't expired
4. For Homey: verify bearer token from athom-cli is current
5. Check logs/ki_system.log for detailed error messages

## Bathroom Automation System (v0.8+)

The bathroom automation system is a self-learning feature that detects shower/bath events and controls dehumidifiers automatically.

**Key Components:**
- `bathroom_automation.py`: Main automation logic for event detection and device control
- `bathroom_analyzer.py`: Analytics and pattern recognition for optimization
- `bathroom_optimizer.py`: Daily background optimization job (runs at 3:00 AM)
- Web UI at `/bathroom` for configuration and `/bathroom/analytics` for visualizations

**How It Works:**
1. Monitors humidity sensors for sudden increases (shower detection)
2. Tracks event duration, peak humidity, temperature changes
3. Controls dehumidifier based on learned thresholds
4. Automatically optimizes thresholds based on historical data (requires min. 3 events, 70% confidence)
5. Provides analytics: event statistics, trends, predictions, common shower times

**Configuration:**
- Stored in `data/bathroom_config.json`
- Includes sensor IDs, device IDs, thresholds (high/low humidity, duration)
- Can be configured via web UI
