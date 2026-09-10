# Configuracion compartida de pytest.

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


ENGINE = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/croply_simulator")
SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def limpiar_tablas() -> None:
	with ENGINE.begin() as connection:
		connection.execute(text("TRUNCATE TABLE lecturas_simuladas, eventos_manuales_pendientes, alertas_simuladas, sensores_simulados, controladores_simulados, parcelas_simuladas RESTART IDENTITY CASCADE"))