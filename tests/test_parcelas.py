from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import SessionLocal
from app.exceptions import ParcelaNoEncontradaError, ParcelaYaExisteError
from app.main import app
from app.models.alerta_simulada import AlertaSimulada
from app.models.controlador_simulado import ControladorSimulado
from app.models.evento_manual_pendiente import EventoManualPendiente
from app.models.lectura_sensor_simulada import LecturaSensorSimulada
from app.models.parcela_simulada import ParcelaSimulada
from app.models.sensor_simulado import SensorSimulado
from app.schemas.parcela import ParcelaRequest
from app.services.parcela_service import crear_parcela, eliminar_parcela, reemplazar_configuracion


def _dto(sensor_ids: list[int] | None = None) -> ParcelaRequest:
	sensor_ids = sensor_ids or [10, 11, 12, 13, 14]
	return ParcelaRequest.model_validate(
		{
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
						{"id": sensor_ids[0], "tipo": "TEMP_HUME_AMBIENTAL"},
						{"id": sensor_ids[1], "tipo": "HUMEDAD_SUELO"},
						{"id": sensor_ids[2], "tipo": "RADIACION_SOLAR"},
						{"id": sensor_ids[3], "tipo": "PRECIPITACION"},
						{"id": sensor_ids[4], "tipo": "PH"},
					],
				}],
			}
		}
	)


def _dto_dos_controladores() -> ParcelaRequest:
	return ParcelaRequest.model_validate(
		{
			"parcela": {
				"id": 1,
				"nombre": "Parcela Norte",
				"latitud": -32.89,
				"longitud": -68.84,
				"controladores": [
					{"id": 3, "ip": "192.168.0.10", "estado": "TRANSMITIENDO", "sensores": [
						{"id": 10, "tipo": "TEMP_HUME_AMBIENTAL"}, {"id": 11, "tipo": "HUMEDAD_SUELO"}
					]},
					{"id": 4, "ip": "192.168.0.20", "estado": "TRANSMITIENDO", "sensores": [
						{"id": 20, "tipo": "RADIACION_SOLAR"}, {"id": 21, "tipo": "PRECIPITACION"}, {"id": 22, "tipo": "PH"}
					]},
				],
			}
		}
	)


def test_crear_parcela_puebla_tablas() -> None:
	db = SessionLocal()
	try:
		crear_parcela(db, _dto())

		assert db.get(ParcelaSimulada, 1) is not None
		assert db.get(ControladorSimulado, 3) is not None
		assert db.query(SensorSimulado).filter(SensorSimulado.parcela_id == 1).count() == 5
	finally:
		db.close()


def test_crear_parcela_con_dos_controladores_puebla_tablas() -> None:
	db = SessionLocal()
	try:
		crear_parcela(db, _dto_dos_controladores())

		assert db.get(ParcelaSimulada, 1) is not None
		assert db.query(ControladorSimulado).filter(ControladorSimulado.parcela_id == 1).count() == 2
		assert db.get(ControladorSimulado, 3) is not None
		assert db.get(ControladorSimulado, 4) is not None
		assert db.query(SensorSimulado).filter(SensorSimulado.controlador_id == 3).count() == 2
		assert db.query(SensorSimulado).filter(SensorSimulado.controlador_id == 4).count() == 3
		assert db.query(SensorSimulado).filter(SensorSimulado.parcela_id == 1).count() == 5
	finally:
		db.close()


def test_crear_parcela_duplicada_lanza_error() -> None:
	db = SessionLocal()
	try:
		dto = _dto()
		crear_parcela(db, dto)

		with pytest.raises(ParcelaYaExisteError):
			crear_parcela(db, dto)
	finally:
		db.close()


def test_reemplazar_configuracion_elimina_sensor_y_historico() -> None:
	db = SessionLocal()
	try:
		crear_parcela(db, _dto())
		db.add(
			LecturaSensorSimulada(
				sensor_id=14,
				parcela_id=1,
				tipo_sensor="PH",
				valor=6.7,
				unidad="pH",
			)
		)
		db.commit()

		reemplazar_configuracion(db, 1, _dto([10, 11, 12, 13, 15]))

		assert db.get(SensorSimulado, 14) is None
		assert db.query(LecturaSensorSimulada).filter(LecturaSensorSimulada.sensor_id == 14).count() == 0
		assert db.get(SensorSimulado, 15) is not None
	finally:
		db.close()


def test_reemplazar_configuracion_puede_pasar_de_uno_a_dos_controladores() -> None:
	db = SessionLocal()
	try:
		crear_parcela(db, _dto())
		reemplazar_configuracion(db, 1, _dto_dos_controladores())
		assert db.query(ControladorSimulado).filter(ControladorSimulado.parcela_id == 1).count() == 2
	finally:
		db.close()


def test_reemplazar_parcela_inexistente_lanza_error() -> None:
	db = SessionLocal()
	try:
		with pytest.raises(ParcelaNoEncontradaError):
			reemplazar_configuracion(db, 1, _dto())
	finally:
		db.close()


def test_eliminar_parcela_borra_dependencias() -> None:
	db = SessionLocal()
	try:
		crear_parcela(db, _dto())
		db.add(
			LecturaSensorSimulada(
				sensor_id=10,
				parcela_id=1,
				tipo_sensor="TEMP_HUME_AMBIENTAL",
				valor=23.4,
				unidad="°C",
			)
		)
		db.commit()

		eliminar_parcela(db, 1)

		assert db.get(ParcelaSimulada, 1) is None
		assert db.query(ControladorSimulado).filter(ControladorSimulado.parcela_id == 1).count() == 0
		assert db.query(SensorSimulado).filter(SensorSimulado.parcela_id == 1).count() == 0
		assert db.query(LecturaSensorSimulada).filter(LecturaSensorSimulada.parcela_id == 1).count() == 0
		assert db.query(AlertaSimulada).filter(AlertaSimulada.parcela_id == 1).count() == 0
		assert db.query(EventoManualPendiente).filter(EventoManualPendiente.parcela_id == 1).count() == 0
	finally:
		db.close()


def test_eliminar_parcela_inexistente_lanza_error() -> None:
	db = SessionLocal()
	try:
		with pytest.raises(ParcelaNoEncontradaError):
			eliminar_parcela(db, 1)
	finally:
		db.close()


def test_post_parcela_integration_crea_recursos() -> None:
	client = TestClient(app)

	response = client.post(
		"/parcelas",
		json={
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
		},
	)

	assert response.status_code == 201


def test_post_parcela_duplicada_integration_devuelve_409() -> None:
	client = TestClient(app)
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
	assert client.post("/parcelas", json=payload).status_code == 409


def test_put_parcela_reemplaza_configuracion() -> None:
	client = TestClient(app)
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
	replacement = {
		"parcela": {
			"id": 1,
			"nombre": "Parcela Norte Actualizada",
			"latitud": -32.9,
			"longitud": -68.85,
			"controladores": [{
				"id": 4,
				"ip": "192.168.0.11",
				"estado": "TRANSMITIENDO",
				"sensores": [
					{"id": 10, "tipo": "TEMP_HUME_AMBIENTAL"},
					{"id": 11, "tipo": "HUMEDAD_SUELO"},
					{"id": 12, "tipo": "RADIACION_SOLAR"},
					{"id": 13, "tipo": "PRECIPITACION"},
				],
			}],
		}
	}

	assert client.post("/parcelas", json=payload).status_code == 201
	assert client.put("/parcelas/1", json=replacement).status_code == 200


def test_put_parcela_inexistente_devuelve_404() -> None:
	client = TestClient(app)
	assert client.put(
		"/parcelas/1",
		json={
			"parcela": {
				"id": 1,
				"nombre": "Parcela Norte",
				"latitud": -32.89,
				"longitud": -68.84,
				"controladores": [{
					"id": 3,
					"ip": "192.168.0.10",
					"estado": "TRANSMITIENDO",
					"sensores": [{"id": 10, "tipo": "TEMP_HUME_AMBIENTAL"}],
				}],
			}
		},
	).status_code == 404


def test_delete_parcela_integration_devuelve_200() -> None:
	client = TestClient(app)
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
	assert client.delete("/parcelas/1").status_code == 200


def test_delete_parcela_inexistente_devuelve_404() -> None:
	client = TestClient(app)
	assert client.delete("/parcelas/1").status_code == 404


def test_post_parcela_invalida_devuelve_422() -> None:
	client = TestClient(app)
	response = client.post(
		"/parcelas",
		json={
			"parcela": {
				"id": 1,
				"nombre": "Parcela Norte",
				"latitud": -32.89,
				"longitud": -68.84,
				"controladores": [{
					"id": 3,
					"ip": "192.168.0.10",
					"estado": "TRANSMITIENDO",
					"sensores": [{"id": 10, "tipo": "HUMEDAD"}],
				}],
			}
		},
	)

	assert response.status_code == 422


def test_post_parcela_con_dos_controladores_integration_crea_recursos() -> None:
	client = TestClient(app)
	response = client.post(
		"/parcelas",
		json={
			"parcela": {
				"id": 1, "nombre": "Parcela Norte", "latitud": -32.89, "longitud": -68.84,
				"controladores": [
					{"id": 3, "ip": "192.168.0.10", "estado": "TRANSMITIENDO", "sensores": [
						{"id": 10, "tipo": "TEMP_HUME_AMBIENTAL"}, {"id": 11, "tipo": "HUMEDAD_SUELO"}
					]},
					{"id": 4, "ip": "192.168.0.20", "estado": "TRANSMITIENDO", "sensores": [
						{"id": 20, "tipo": "RADIACION_SOLAR"}, {"id": 21, "tipo": "PRECIPITACION"}, {"id": 22, "tipo": "PH"}
					]},
				],
			}
		},
	)
	assert response.status_code == 201
	estado = client.get("/parcelas/1/estado")
	assert estado.status_code == 200
	assert len(estado.json()["controladores"]) == 2


def test_post_parcela_sin_controladores_devuelve_422() -> None:
	client = TestClient(app)
	response = client.post(
		"/parcelas",
		json={"parcela": {"id": 1, "nombre": "Parcela Norte", "latitud": -32.89, "longitud": -68.84, "controladores": []}},
	)
	assert response.status_code == 422


def test_post_parcela_con_ids_de_controlador_duplicados_devuelve_422() -> None:
	client = TestClient(app)
	response = client.post(
		"/parcelas",
		json={
			"parcela": {
				"id": 1, "nombre": "Parcela Norte", "latitud": -32.89, "longitud": -68.84,
				"controladores": [
					{"id": 3, "ip": "192.168.0.10", "estado": "TRANSMITIENDO", "sensores": [{"id": 10, "tipo": "PH"}]},
					{"id": 3, "ip": "192.168.0.20", "estado": "TRANSMITIENDO", "sensores": [{"id": 11, "tipo": "RADIACION_SOLAR"}]},
				],
			}
		},
	)
	assert response.status_code == 422