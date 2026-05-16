"""
weather.py — Real-time weather data via OpenWeatherMap API.
"""

import re
from typing import Optional, TypedDict
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from .config import settings
from .utils import logger, Timer, ttl_cached, cache_key, get_cached, set_cached

# ── Config ──────────────────────────────────────────────────────────────────
OWM_BASE = "https://api.openweathermap.org/data/2.5/weather"
UNITS = "metric"   # metric → °C; imperial → °F; standard → K

class WeatherData(TypedDict):
    city: str
    country: str
    temp_c: float
    feels_like_c: float
    humidity: int
    description: str
    wind_speed_ms: float
    visibility_km: float

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True
)
async def fetch_weather(city: str) -> WeatherData:
    """
    Fetch current weather for a city from OpenWeatherMap with retries.
    """
    # ── Cache check ─────────────────────────────────────────────────────────
    key = cache_key("weather", city.lower())
    cached = get_cached(key)
    if cached:
        logger.debug(f"Weather cache HIT — city={city}")
        return cached

    api_key = settings.WEATHER_API_KEY
    if not api_key:
        raise ValueError("Weather API key not configured.")
        
    params = {
        "q": city,
        "appid": api_key,
        "units": UNITS,
    }

    logger.info(f"Fetching weather for: {city}")
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(OWM_BASE, params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ValueError(f"City '{city}' not found.")
            raise
        except Exception as exc:
            logger.error(f"Weather API request failed: {exc}")
            raise

    data = resp.json()
    result: WeatherData = {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temp_c": round(data["main"]["temp"], 1),
        "feels_like_c": round(data["main"]["feels_like"], 1),
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"].capitalize(),
        "wind_speed_ms": round(data["wind"]["speed"], 1),
        "visibility_km": round(data.get("visibility", 0) / 1000, 1),
    }

    set_cached(key, result)
    return result

def weather_to_context(data: WeatherData) -> str:
    """
    Convert WeatherData into a concise, LLM-friendly context string.
    """
    return (
        f"Current weather in {data['city']}, {data['country']}: "
        f"{data['temp_c']}°C (feels like {data['feels_like_c']}°C), "
        f"{data['description']}, "
        f"humidity {data['humidity']}%, "
        f"wind {data['wind_speed_ms']} m/s, "
        f"visibility {data['visibility_km']} km."
    )
