from __future__ import annotations

from unittest.mock import Mock, patch

import httpx
import pytest

from app.exceptions import OpenMeteoError
from app.services.openmeteo_service import obtener_clima_actual


def test_obtener_clima_actual_mapea_datos_correctamente() -> None:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "current": {
            "temperature_2m": 23,
            "relative_humidity_2m": 64,
            "shortwave_radiation": 550,
            "precipitation": 0.8,
            "cloud_cover": 35,
            "wind_speed_10m": 4,
        }
    }

    with patch("httpx.Client.get", return_value=response) as mocked_get:
        datos = obtener_clima_actual(-32.89, -68.84)

    assert mocked_get.called
    assert datos == {
        "temperature_2m": 23.0,
        "relative_humidity_2m": 64.0,
        "shortwave_radiation": 550.0,
        "precipitation": 0.8,
        "cloud_cover": 35.0,
        "wind_speed_10m": 4.0,
    }


def test_obtener_clima_actual_lanza_error_en_timeout() -> None:
    with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
        with pytest.raises(OpenMeteoError):
            obtener_clima_actual(-32.89, -68.84)


def test_obtener_clima_actual_lanza_error_si_faltan_variables() -> None:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"current": {"temperature_2m": 23.0}}

    with patch("httpx.Client.get", return_value=response):
        with pytest.raises(OpenMeteoError):
            obtener_clima_actual(-32.89, -68.84)