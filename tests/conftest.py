"""Infraestrutura dos testes.

O banco é um SQLite em memória: o `get_db` da aplicação é substituído por uma sessão
ligada a ele, então as rotas, os use cases e os repositories rodam exatamente como em
produção — só o motor do banco muda. Cada teste começa com o schema recriado do zero.
"""

import os

# Precisa vir antes de qualquer import de `src`: o engine é construído no import de
# src.database.database. Assim os testes não dependem de um .env válido nem de um MySQL.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from datetime import datetime, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import src.models  # noqa: F401,E402  — registra as 8 tabelas no metadata
from src.database.database import Base, get_db  # noqa: E402
from src.main import app  # noqa: E402

#: Referência de tempo dos testes. Os voos são sempre criados no futuro para não
#: esbarrarem na regra de "partida futura" da realocação.
AGORA = datetime.now().replace(microsecond=0)


@pytest.fixture
def engine():
    motor = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(motor, "connect")
    def _ativar_chaves_estrangeiras(conexao, _registro):
        # O SQLite ignora ON DELETE CASCADE se as FKs não forem ligadas explicitamente.
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(motor)
    yield motor
    Base.metadata.drop_all(motor)
    motor.dispose()


@pytest.fixture
def db(engine):
    sessao = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    try:
        yield sessao
    finally:
        sessao.close()


@pytest.fixture
def client(db):
    """Cliente HTTP da API apontando para o banco de teste."""

    def _sessao_de_teste():
        yield db

    app.dependency_overrides[get_db] = _sessao_de_teste
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


# --- Fábricas ----------------------------------------------------------------
# Tudo é criado pela própria API, então as fixtures também exercitam os endpoints
# de escrita em vez de inserir direto no banco.


def criar_terminal(client, nome="Terminal Nacional", tipo="NACIONAL") -> dict:
    resposta = client.post("/api/terminais", json={"nome": nome, "tipo": tipo})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_aeronave(client, prefixo="ZS-TST", capacidade=6) -> dict:
    resposta = client.post(
        "/api/aeronaves",
        json={
            "prefixo": prefixo,
            "modelo": "Cessna 208",
            "companhia": "Teste Air",
            "capacidade": capacidade,
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_voo(
    client,
    aeronave_id: int,
    terminal_id: int,
    codigo="TS100",
    origem="CPT",
    destino="JNB",
    horas_ate_partida=4,
) -> dict:
    partida = AGORA + timedelta(hours=horas_ate_partida)
    resposta = client.post(
        "/api/voos",
        json={
            "codigo": codigo,
            "origem": origem,
            "destino": destino,
            "partida_prevista": partida.isoformat(),
            "chegada_prevista": (partida + timedelta(hours=2)).isoformat(),
            "aeronave_id": aeronave_id,
            "terminal_id": terminal_id,
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_passageiro(client, nome="Ada Lovelace", documento="DOC-001") -> dict:
    resposta = client.post(
        "/api/passageiros", json={"nome": nome, "documento": documento}
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_vaga(client, terminal_id: int, codigo="A1", tipo="GATE") -> dict:
    resposta = client.post(
        "/api/vagas",
        json={"codigo": codigo, "terminal_id": terminal_id, "tipo": tipo},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_reserva(client, passageiro_id: int, voo_id: int, assento=None) -> dict:
    corpo = {"passageiro_id": passageiro_id, "voo_id": voo_id}
    if assento:
        corpo["assento"] = assento
    resposta = client.post("/api/reservas", json=corpo)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


# --- Fixtures de cenário -----------------------------------------------------


@pytest.fixture
def terminal(client) -> dict:
    return criar_terminal(client)


@pytest.fixture
def aeronave(client) -> dict:
    return criar_aeronave(client)


@pytest.fixture
def voo(client, aeronave, terminal) -> dict:
    return criar_voo(client, aeronave["id"], terminal["id"])


@pytest.fixture
def passageiro(client) -> dict:
    return criar_passageiro(client)


@pytest.fixture
def reserva(client, passageiro, voo) -> dict:
    return criar_reserva(client, passageiro["id"], voo["id"])
