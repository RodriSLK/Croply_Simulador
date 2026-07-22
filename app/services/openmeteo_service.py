from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.exceptions import OpenMeteoError


def obtener_clima_actual(latitud: float, longitud: float) -> dict[str, float]:
	params = {
		"latitude": latitud,
		"longitude": longitud,
		"current": "temperature_2m,relative_humidity_2m,shortwave_radiation,precipitation,cloud_cover,wind_speed_10m",
		"timezone": "UTC",
	}

	try:
		with httpx.Client(timeout=10.0) as client:
			response = client.get(settings.OPEN_METEO_BASE_URL, params=params)
			response.raise_for_status()
			payload = response.json()

		current = payload["current"]
		return {
			"temperature_2m": float(current["temperature_2m"]),
			"relative_humidity_2m": float(current["relative_humidity_2m"]),
			"shortwave_radiation": float(current["shortwave_radiation"]),
			"precipitation": float(current["precipitation"]),
			"cloud_cover": float(current["cloud_cover"]),
			"wind_speed_10m": float(current["wind_speed_10m"]),
		}
	except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
		raise OpenMeteoError("No fue posible obtener datos climáticos desde Open-Meteo") from exc