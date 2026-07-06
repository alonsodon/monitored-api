import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Task


@pytest.fixture(scope="function")
def db_session():
    """BD SQLite en memoria, nueva para cada test (aislamiento total)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)  # crea las tablas desde los modelos
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    yield session  # el test usa la sesión aquí
    session.close()
    Base.metadata.drop_all(bind=engine)  # limpieza: borra todo al terminar


@pytest.fixture(scope="function")
def client(db_session):
    """Cliente HTTP que usa la BD de test en lugar de la real."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db  # truco clave
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_task(db_session) -> Task:
    """Una tarea ya guardada, lista para tests que necesitan datos previos."""
    task = Task(title="Test Task")
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task
