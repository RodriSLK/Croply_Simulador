from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _crear_parcela(client: TestClient) -> None:
	payload = {
		"parcela": {
			"id": 1,
			"nombre": "Parcela Norte",
			"latitud": -32.89,
			"longitud": -68.84,
			"controladores": [{
				"id": 3,
				"ip": "192.168.0.10",
				"estado": "TRANSMITIENDO",
				"sensores": [
					{"id": 10, "tipo": "TEMP_HUME_AMBIENTAL"},
					{"id": 11, "tipo": "HUMEDAD_SUELO"},
					{"id": 12, "tipo": "RADIACION_SOLAR"},
					{"id": 13, "tipo": "PRECIPITACION"},
					{"id": 14, "tipo": "PH"},
				],
			}],
		}
	}
	assert client.post("/parcelas", json=payload).status_code == 201


def test_estado_parcela_nueva_devuelve_null_en_lecturas() -> None:
	client = TestClient(app)
	_crear_parcela(client)

	response = client.get("/parcelas/1/estado")

	assert response.status_code == 200
	body = response.json()
	assert body["parcela_id"] == 1
	assert body["controladores"][0]["sensores"][0]["valor_actual"] is None
	assert body["controladores"][0]["sensores"][0]["fecha_ultima_lectura"] is None


def test_estado_parcela_con_dos_controladores() -> None:
	client = TestClient(app)
	payload = {
		"parcela": {
			"id": 2, "nombre": "Parcela Sur", "latitud": -32.9, "longitud": -68.85,
			"controladores": [
				{"id": 20, "ip": "192.168.0.20", "estado": "TRANSMITIENDO", "sensores": [{"id": 200, "tipo": "PH"}]},
				{"id": 21, "ip": "192.168.0.21", "estado": "TRANSMITIENDO", "sensores": [{"id": 210, "tipo": "HUMEDAD_SUELO"}]},
			],
		}
	}
	assert client.post("/parcelas", json=payload).status_code == 201
	response = client.get("/parcelas/2/estado")
	assert response.status_code == 200
	body = response.json()
	assert body["parcela_id"] == 2
	assert len(body["controladores"]) == 2
	ids_controlador = {controlador["controlador_id"] for controlador in body["controladores"]}
	assert ids_controlador == {20, 21}


def test_estado_parcela_inexistente_devuelve_404() -> None:
	client = TestClient(app)

	response = client.get("/parcelas/999/estado")

	assert response.status_code == 404