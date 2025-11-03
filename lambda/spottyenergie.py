import requests
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from utils import get_datetime_vienna

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class PriceData:
    from_time: datetime
    price: float


class _SpottyEnergieApi:

    def __init__(self):
        api_key = os.environ.get("SPOTTY_API_KEY", "<key>")
        self.API_URL = f"https://i.spottyenergie.at/api/prices/MARKET/{api_key}?timezone=at"
        self._data: Optional[List[PriceData]] = None
        self._last_update: Optional[datetime] = None

    def _should_reload(self) -> bool:
        if self._data is None or self._last_update is None:
            return True

        now_utc = datetime.now(timezone.utc)

        today_noon_utc = now_utc.replace(hour=12, minute=0, second=0, microsecond=0)

        # If it's after noon UTC and we last updated before that, reload
        if now_utc >= today_noon_utc and self._last_update < today_noon_utc:
            return True

        return False

    def _get_filtered_prices(self, date: datetime) -> List[PriceData]:
        return [p for p in self._get_prices() if p.from_time.date() == date.date()]
    
    def _get_cheapest_hours(self, prices: List[PriceData], hours: int) -> List[PriceData]:
        prices_per_hour = 4
        block_size = hours * prices_per_hour

        min_avg = float('inf')
        min_block = None
        for i in range(len(prices) - block_size + 1):
            block = prices[i:i+block_size]
            avg_price = sum(p.price for p in block) / block_size
            if avg_price < min_avg:
                min_avg = avg_price
                min_block = block
        return min_block

    def _get_prices(self) -> List[PriceData]:
        if not self._should_reload():
            return self._data

        response = requests.get(self.API_URL)
        response.raise_for_status()

        self._data = [
            PriceData(
                from_time=datetime.fromisoformat(item['from']),
                price=item['price']
            )
            for item in response.json()
        ]
        self._last_update = datetime.now(timezone.utc)

        return self._data

    def get_today_prices(self) -> List[PriceData]:
        today_date = get_datetime_vienna()
        return self._get_filtered_prices(today_date)

    def get_tomorrow_prices(self) -> List[PriceData]:
        tomorrow_date = get_datetime_vienna() + timedelta(days=1)
        return self._get_filtered_prices(tomorrow_date)
    
    def get_cheapest_hours_today(self, hours: int) -> List[PriceData]:
        today_prices = self.get_today_prices()
        return self._get_cheapest_hours(today_prices, hours)

    def get_cheapest_hours_tomorrow(self, hours: int) -> List[PriceData]:
        tomorrow_prices = self.get_tomorrow_prices()
        return self._get_cheapest_hours(tomorrow_prices, hours)


spotty_energie_api = _SpottyEnergieApi()


def handle_api_exception(func):
    def wrapper(*args, **kwargs):
        args = args if args is not None else ()
        kwargs = kwargs if kwargs is not None else {}
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException:
            logger.error(f"RequestException: {e}")
            return "Entschuldigung, ich konnte die Strompreis-Datenbank gerade nicht erreichen. Bitte versuche es später erneut."
        except (KeyError, ValueError, TypeError, IndexError) as e:
            logger.error(f"Data error: {e}")
            return f"Entschuldigung, die erhaltenen Preisdaten waren fehlerhaft oder konnten nicht gelesen werden. {e}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return "Es ist ein unerwarteter technischer Fehler aufgetreten."
    return wrapper
