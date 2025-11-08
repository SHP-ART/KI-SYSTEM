"""Strompreis-Daten Sammler"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class EnergyPriceCollector:
    """Sammelt dynamische Strompreise von verschiedenen Anbietern"""

    def __init__(self, provider: str = "awattar", api_key: str = None):
        self.provider = provider.lower()
        self.api_key = api_key

    def get_awattar_prices(self, country: str = "de") -> Optional[Dict]:
        """
        Holt Strompreise von aWATTar (Deutschland & Österreich)
        API ist kostenlos und ohne Key nutzbar
        https://www.awattar.de/
        """
        try:
            if country.lower() == "at":
                url = "https://api.awattar.at/v1/marketdata"
            else:
                url = "https://api.awattar.de/v1/marketdata"

            # Aktuelle Stunde bis +24h
            start = datetime.now().replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=24)

            params = {
                'start': int(start.timestamp() * 1000),
                'end': int(end.timestamp() * 1000)
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            prices = []
            for item in data['data']:
                prices.append({
                    'start_time': datetime.fromtimestamp(item['start_timestamp'] / 1000).isoformat(),
                    'end_time': datetime.fromtimestamp(item['end_timestamp'] / 1000).isoformat(),
                    'price_per_kwh': item['marketprice'] / 1000,  # Convert to EUR/kWh
                    'unit': 'EUR/kWh'
                })

            # Finde günstigste und teuerste Stunde
            current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
            current_price = None

            for price in prices:
                if price['start_time'].startswith(current_hour.isoformat()[:13]):
                    current_price = price['price_per_kwh']
                    break

            min_price = min(prices, key=lambda x: x['price_per_kwh'])
            max_price = max(prices, key=lambda x: x['price_per_kwh'])
            avg_price = sum(p['price_per_kwh'] for p in prices) / len(prices)

            return {
                'timestamp': datetime.now().isoformat(),
                'provider': 'awattar',
                'current_price': current_price,
                'average_price': avg_price,
                'min_price': min_price['price_per_kwh'],
                'min_price_time': min_price['start_time'],
                'max_price': max_price['price_per_kwh'],
                'max_price_time': max_price['start_time'],
                'hourly_prices': prices,
                'unit': 'EUR/kWh'
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"aWATTar API error: {e}")
            return None

    def get_tibber_prices(self) -> Optional[Dict]:
        """
        Holt Strompreise von Tibber
        Benötigt API-Token: https://developer.tibber.com/
        """
        if not self.api_key:
            logger.warning("Tibber API key required")
            return None

        try:
            url = "https://api.tibber.com/v1-beta/gql"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            query = """
            {
              viewer {
                homes {
                  currentSubscription {
                    priceInfo {
                      current {
                        total
                        energy
                        tax
                        startsAt
                      }
                      today {
                        total
                        startsAt
                      }
                      tomorrow {
                        total
                        startsAt
                      }
                    }
                  }
                }
              }
            }
            """

            response = requests.post(
                url,
                headers=headers,
                json={'query': query},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            home = data['data']['viewer']['homes'][0]
            price_info = home['currentSubscription']['priceInfo']

            current = price_info['current']
            today_prices = price_info['today']

            return {
                'timestamp': datetime.now().isoformat(),
                'provider': 'tibber',
                'current_price': current['total'],
                'current_energy_price': current['energy'],
                'current_tax': current['tax'],
                'current_starts_at': current['startsAt'],
                'today_prices': today_prices,
                'tomorrow_prices': price_info.get('tomorrow', []),
                'unit': 'EUR/kWh'
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Tibber API error: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Tibber data parsing error: {e}")
            return None

    def get_prices(self) -> Optional[Dict]:
        """
        Hauptmethode - holt Preise vom konfigurierten Anbieter
        """
        if self.provider == "awattar":
            return self.get_awattar_prices()
        elif self.provider == "tibber":
            return self.get_tibber_prices()
        else:
            logger.error(f"Unknown energy provider: {self.provider}")
            return None

    def is_cheap_hour(self, threshold_percentile: float = 0.3) -> bool:
        """
        Prüft, ob die aktuelle Stunde zu den günstigen gehört
        threshold_percentile: 0.3 = günstigste 30% der Stunden
        """
        prices = self.get_prices()

        if not prices or 'current_price' not in prices:
            return False

        current = prices['current_price']

        if 'hourly_prices' in prices:
            all_prices = [p['price_per_kwh'] for p in prices['hourly_prices']]
        elif 'today_prices' in prices:
            all_prices = [p['total'] for p in prices['today_prices']]
        else:
            return False

        sorted_prices = sorted(all_prices)
        threshold_index = int(len(sorted_prices) * threshold_percentile)
        threshold_price = sorted_prices[threshold_index]

        return current <= threshold_price

    def get_cheapest_hours(self, count: int = 3) -> List[Dict]:
        """
        Findet die günstigsten Stunden des Tages
        Nützlich für zeitgesteuerte Verbraucher (Waschmaschine, etc.)
        """
        prices = self.get_prices()

        if not prices:
            return []

        if 'hourly_prices' in prices:
            all_prices = prices['hourly_prices']
        elif 'today_prices' in prices:
            all_prices = [
                {
                    'start_time': p['startsAt'],
                    'price_per_kwh': p['total']
                }
                for p in prices['today_prices']
            ]
        else:
            return []

        sorted_prices = sorted(all_prices, key=lambda x: x['price_per_kwh'])
        return sorted_prices[:count]
