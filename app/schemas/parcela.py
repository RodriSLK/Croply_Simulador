from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums.enums import EstadoTransmision, TipoSensorEnum

class SensorEntrada(BaseModel):
	id: int
	tipo: TipoSensorEnum


class ControladorEntrada(BaseModel):
	id: int
	ip: str | None = None
	estado: EstadoTransmision
	sensores: list[SensorEntrada]


class ParcelaEntrada(BaseModel):
	id: int
	nombre: str
	latitud: float
	longitud: float
	controladores: list[ControladorEntrada] = Field(min_length=1)

	@field_validator("controladores")
	@classmethod
	def _ids_de_controlador_unicos(cls, controladores: list[ControladorEntrada]) -> list[ControladorEntrada]:
		ids = [controlador.id for controlador in controladores]
		if len(ids) != len(set(ids)):
			raise ValueError("Los ids de controlador dentro de una misma parcela deben ser únicos")
		return controladores


class ParcelaRequest(BaseModel):
	parcela: ParcelaEntrada


class SensorEstado(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	sensor_id: int
	tipo: TipoSensorEnum
	valor_actual: float | None = None
	unidad: str | None = None
	fecha_ultima_lectura: datetime | None = None


class ControladorEstado(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	controlador_id: int
	sensores: list[SensorEstado]


class ParcelaEstadoResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	parcela_id: int
	nombre: str
	timestamp_simulacion: datetime | None = None
	controladores: list[ControladorEstado]

class ParcelaListItem(BaseModel):
	model_config = ConfigDict(from_attributes=True)
	parcela_id: int
	nombre: str


class ParcelasListResponse(BaseModel):
	parcelas: list[ParcelaListItem]