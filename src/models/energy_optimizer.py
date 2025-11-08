"""Energieoptimierungs-Modul"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from loguru import logger


class EnergyOptimizer:
    """
    Optimiert Energieverbrauch basierend auf:
    - Dynamischen Strompreisen
    - Wettervorhersage
    - Nutzerpräferenzen
    - Komfort-Anforderungen
    """

    def __init__(self, config: Dict):
        self.min_temperature = config.get('min_temperature', 18.0)
        self.max_temperature = config.get('max_temperature', 23.0)
        self.comfort_priority = config.get('comfort_priority', 0.7)  # 0-1

    def calculate_energy_price_level(self, current_price: float,
                                     hourly_prices: List[Dict]) -> int:
        """
        Berechnet Preis-Level: 1=günstig, 2=mittel, 3=teuer

        Args:
            current_price: Aktueller Strompreis
            hourly_prices: Liste aller Preise des Tages
        """
        if not hourly_prices:
            return 2  # Default: mittel

        prices = [p.get('price_per_kwh', p.get('total', 0)) for p in hourly_prices]
        prices = [p for p in prices if p > 0]  # Filter ungültige Werte

        if not prices:
            return 2

        # Berechne Perzentile
        p33 = np.percentile(prices, 33)
        p66 = np.percentile(prices, 66)

        if current_price <= p33:
            return 1  # Günstig
        elif current_price <= p66:
            return 2  # Mittel
        else:
            return 3  # Teuer

    def should_preheat(self, forecast: List[Dict], current_temp: float,
                      target_temp: float) -> Tuple[bool, Optional[datetime]]:
        """
        Entscheidet, ob vorgeheizt werden sollte während günstiger Strompreise

        Returns:
            (should_preheat, optimal_time)
        """
        if current_temp >= target_temp:
            return False, None

        # Finde günstigste Stunden
        cheap_hours = [
            f for f in forecast
            if f.get('energy_price_level', 2) == 1
        ]

        if not cheap_hours:
            return False, None

        # Prüfe ob es sinnvoll ist (nächste 6 Stunden)
        now = datetime.now()
        next_6h = [
            h for h in cheap_hours
            if datetime.fromisoformat(h['timestamp']) < now + timedelta(hours=6)
        ]

        if next_6h:
            optimal_time = datetime.fromisoformat(next_6h[0]['timestamp'])
            return True, optimal_time

        return False, None

    def optimize_heating_schedule(self, forecast: List[Dict],
                                  presence_schedule: List[Dict]) -> List[Dict]:
        """
        Erstellt optimalen Heiz-Plan basierend auf:
        - Strompreisen
        - Anwesenheit
        - Wetter

        Args:
            forecast: Wetter- und Preis-Vorhersage für nächste 24h
            presence_schedule: Anwesenheits-Plan [{timestamp, is_home}]

        Returns:
            Optimierter Temperatur-Plan
        """
        schedule = []

        for hour_data in forecast:
            timestamp = datetime.fromisoformat(hour_data['timestamp'])

            # Prüfe Anwesenheit
            presence = self._get_presence_at_time(presence_schedule, timestamp)

            # Basis-Temperatur basierend auf Anwesenheit
            if presence:
                base_temp = 21.0
            else:
                base_temp = 18.0

            # Anpassung basierend auf Energiepreis
            price_level = hour_data.get('energy_price_level', 2)
            outdoor_temp = hour_data.get('outdoor_temperature', 10.0)

            # Bei hohen Außentemperaturen weniger heizen
            if outdoor_temp > 15:
                base_temp -= 1.0

            # Bei teuren Preisen und Abwesenheit stark reduzieren
            if price_level == 3 and not presence:
                target_temp = self.min_temperature
            elif price_level == 3 and presence:
                target_temp = base_temp - 1.0
            elif price_level == 1:
                target_temp = base_temp + 0.5  # Vorheizen bei günstigen Preisen
            else:
                target_temp = base_temp

            # Komfort-Priorität anwenden
            if presence:
                # Bei hoher Komfort-Priorität weniger stark optimieren
                comfort_adjustment = (1 - self.comfort_priority) * (base_temp - target_temp)
                target_temp = base_temp - comfort_adjustment

            # Sichere Grenzen
            target_temp = max(self.min_temperature, min(self.max_temperature, target_temp))

            # Berechne geschätzte Kosten
            estimated_cost = self._estimate_heating_cost(
                target_temp,
                outdoor_temp,
                hour_data.get('price_per_kwh', 0.3)
            )

            schedule.append({
                'timestamp': hour_data['timestamp'],
                'target_temperature': round(target_temp, 1),
                'outdoor_temperature': outdoor_temp,
                'price_level': price_level,
                'presence': presence,
                'estimated_cost_euro': estimated_cost,
                'reasoning': self._explain_decision(
                    target_temp, base_temp, price_level, presence
                )
            })

        return schedule

    def _get_presence_at_time(self, presence_schedule: List[Dict],
                             timestamp: datetime) -> bool:
        """Ermittelt ob jemand zu einem Zeitpunkt zu Hause ist"""
        for entry in presence_schedule:
            entry_time = datetime.fromisoformat(entry['timestamp'])
            if abs((entry_time - timestamp).total_seconds()) < 1800:  # 30 min Toleranz
                return entry.get('is_home', True)

        # Default: tagsüber wahrscheinlich nicht zu Hause
        hour = timestamp.hour
        is_weekend = timestamp.weekday() >= 5

        if is_weekend:
            return True  # Am Wochenende meistens zu Hause

        # Werktags: zu Hause morgens/abends
        return hour < 8 or hour >= 18

    def _estimate_heating_cost(self, target_temp: float,
                              outdoor_temp: float,
                              price_per_kwh: float) -> float:
        """
        Schätzt Heizkosten pro Stunde

        Vereinfachte Berechnung:
        - Je größer die Temperaturdifferenz, desto mehr Energie
        - Durchschnittliche Wohnung: ~1 kW pro 10°C Differenz
        """
        temp_diff = max(0, target_temp - outdoor_temp)

        # Geschätzter Verbrauch in kWh pro Stunde
        estimated_kwh = (temp_diff / 10) * 1.5

        cost = estimated_kwh * price_per_kwh

        return round(cost, 2)

    def _explain_decision(self, target_temp: float, base_temp: float,
                         price_level: int, presence: bool) -> str:
        """Erklärt die Entscheidung in natürlicher Sprache"""
        reasons = []

        if not presence:
            reasons.append("Niemand zu Hause - Eco-Modus")

        if price_level == 1:
            reasons.append("Günstiger Strompreis - Vorheizen")
        elif price_level == 3:
            reasons.append("Teurer Strompreis - Reduzierung")

        if target_temp < base_temp:
            saving = round((base_temp - target_temp) * 0.5, 1)
            reasons.append(f"~{saving}% Energieeinsparung")

        return " | ".join(reasons) if reasons else "Normalbetrieb"

    def calculate_savings(self, actual_schedule: List[Dict],
                         optimized_schedule: List[Dict]) -> Dict:
        """
        Berechnet geschätzte Einsparungen durch Optimierung

        Args:
            actual_schedule: Tatsächlicher/alter Plan
            optimized_schedule: Optimierter Plan

        Returns:
            Einsparungen und Statistiken
        """
        actual_cost = sum(h.get('estimated_cost_euro', 0) for h in actual_schedule)
        optimized_cost = sum(h.get('estimated_cost_euro', 0) for h in optimized_schedule)

        savings = actual_cost - optimized_cost
        savings_percent = (savings / actual_cost * 100) if actual_cost > 0 else 0

        return {
            'daily_savings_euro': round(savings, 2),
            'savings_percent': round(savings_percent, 1),
            'monthly_savings_euro': round(savings * 30, 2),
            'yearly_savings_euro': round(savings * 365, 2),
            'actual_cost': round(actual_cost, 2),
            'optimized_cost': round(optimized_cost, 2)
        }

    def get_smart_recommendations(self, current_state: Dict,
                                 forecast: List[Dict]) -> List[str]:
        """
        Gibt intelligente Empfehlungen zur Energieeinsparung

        Returns:
            Liste von Empfehlungen als Strings
        """
        recommendations = []

        # Prüfe aktuelle Situation
        current_temp = current_state.get('current_temperature', 20)
        outdoor_temp = current_state.get('outdoor_temperature', 10)
        price_level = current_state.get('energy_price_level', 2)

        # Empfehlung 1: Preisbasiert
        if price_level == 3:
            recommendations.append(
                "💡 Strompreis ist aktuell hoch. "
                "Temperatur um 1°C senken spart ca. 6% Energie."
            )

        # Empfehlung 2: Vorheizen
        cheap_hours = [f for f in forecast[:6] if f.get('energy_price_level') == 1]
        if cheap_hours:
            time = datetime.fromisoformat(cheap_hours[0]['timestamp']).strftime('%H:%M')
            recommendations.append(
                f"⚡ Günstiger Strom ab {time} Uhr. "
                f"Vorheizen kann Kosten sparen."
            )

        # Empfehlung 3: Wetter
        if outdoor_temp > 15:
            recommendations.append(
                f"🌡️ Außentemperatur ist {outdoor_temp}°C. "
                f"Heizung kann reduziert werden."
            )

        # Empfehlung 4: Temperatur zu hoch
        if current_temp > 22 and price_level >= 2:
            recommendations.append(
                "📉 Aktuelle Temperatur ist relativ hoch. "
                "Jedes Grad weniger spart ca. 6% Energie."
            )

        return recommendations
