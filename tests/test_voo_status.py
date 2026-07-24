"""Máquina de estados do voo (TRANSICOES_VOO) e os efeitos colaterais de cada estado."""

import pytest

from tests.conftest import criar_vaga

TRANSICOES_VALIDAS = [
    ("NO_HORARIO", "ATRASADO"),
    ("NO_HORARIO", "EMBARQUE"),
    ("NO_HORARIO", "CANCELADO"),
    ("ATRASADO", "EMBARQUE"),
    ("ATRASADO", "CANCELADO"),
    ("EMBARQUE", "FINALIZADO"),
    ("EMBARQUE", "CANCELADO"),
]

TRANSICOES_INVALIDAS = [
    ("NO_HORARIO", "FINALIZADO"),
    ("ATRASADO", "NO_HORARIO"),
    ("EMBARQUE", "ATRASADO"),
    ("FINALIZADO", "EMBARQUE"),
    ("CANCELADO", "NO_HORARIO"),
]

#: Caminho mais curto até cada estado, para montar o cenário de cada teste.
CAMINHO_ATE = {
    "NO_HORARIO": [],
    "ATRASADO": ["ATRASADO"],
    "EMBARQUE": ["EMBARQUE"],
    "FINALIZADO": ["EMBARQUE", "FINALIZADO"],
    "CANCELADO": ["CANCELADO"],
}


def levar_ate(client, voo_id: int, estado: str) -> None:
    for passo in CAMINHO_ATE[estado]:
        resposta = client.patch(f"/api/voos/{voo_id}/status", json={"status": passo})
        assert resposta.status_code == 200, resposta.text


@pytest.mark.parametrize("origem,destino", TRANSICOES_VALIDAS)
def test_transicao_valida_muda_o_status(client, voo, origem, destino):
    levar_ate(client, voo["id"], origem)

    resposta = client.patch(f"/api/voos/{voo['id']}/status", json={"status": destino})

    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["status"] == destino


@pytest.mark.parametrize("origem,destino", TRANSICOES_INVALIDAS)
def test_transicao_invalida_devolve_409(client, voo, origem, destino):
    levar_ate(client, voo["id"], origem)

    resposta = client.patch(f"/api/voos/{voo['id']}/status", json={"status": destino})

    assert resposta.status_code == 409, resposta.text
    assert resposta.json()["codigo"] == "CONFLITO"
    # A mensagem precisa dizer quais transições seriam aceitas.
    assert "Transições permitidas" in resposta.json()["detail"]


@pytest.mark.parametrize("terminal_", ["FINALIZADO", "CANCELADO"])
def test_estados_terminais_nao_oferecem_transicao(client, voo, terminal_):
    levar_ate(client, voo["id"], terminal_)

    resposta = client.get(f"/api/voos/{voo['id']}")

    assert resposta.json()["transicoes_permitidas"] == []


def test_transicoes_permitidas_acompanham_o_status_atual(client, voo):
    assert sorted(voo["transicoes_permitidas"]) == ["ATRASADO", "CANCELADO", "EMBARQUE"]

    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "EMBARQUE"})

    atual = client.get(f"/api/voos/{voo['id']}").json()
    assert sorted(atual["transicoes_permitidas"]) == ["CANCELADO", "FINALIZADO"]


def test_repetir_o_mesmo_status_e_aceito_sem_erro(client, voo):
    resposta = client.patch(f"/api/voos/{voo['id']}/status", json={"status": "NO_HORARIO"})

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "NO_HORARIO"


def test_embarque_registra_a_partida_real(client, voo):
    assert voo["partida_real"] is None

    resposta = client.patch(f"/api/voos/{voo['id']}/status", json={"status": "EMBARQUE"})

    assert resposta.json()["partida_real"] is not None


def test_finalizar_promove_check_in_para_embarcada(client, voo, reserva):
    client.patch(f"/api/reservas/{reserva['id']}/check-in")
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "EMBARQUE"})

    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "FINALIZADO"})

    atual = client.get(f"/api/reservas/{reserva['id']}").json()
    assert atual["status"] == "EMBARCADA"


def test_finalizar_registra_chegada_e_libera_a_vaga(client, voo, terminal):
    vaga = criar_vaga(client, terminal["id"])
    client.post(f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga["id"]})
    assert client.get(f"/api/vagas/{vaga['id']}").json()["status"] == "OCUPADA"

    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "EMBARQUE"})
    resposta = client.patch(f"/api/voos/{voo['id']}/status", json={"status": "FINALIZADO"})

    assert resposta.json()["chegada_real"] is not None
    assert client.get(f"/api/vagas/{vaga['id']}").json()["status"] == "LIVRE"
    alocacao = client.get(f"/api/voos/{voo['id']}/alocacoes").json()[0]
    assert alocacao["ativa"] is False
    assert alocacao["fim"] is not None


def test_cancelar_derruba_as_reservas_ativas_em_cascata(client, voo, reserva):
    client.patch(f"/api/reservas/{reserva['id']}/check-in")

    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "CANCELADO"})

    assert client.get(f"/api/reservas/{reserva['id']}").json()["status"] == "CANCELADA"


def test_cancelar_devolve_a_vaga(client, voo, terminal):
    vaga = criar_vaga(client, terminal["id"])
    client.post(f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga["id"]})

    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "CANCELADO"})

    assert client.get(f"/api/vagas/{vaga['id']}").json()["status"] == "LIVRE"


def test_voo_inexistente_devolve_404(client):
    resposta = client.patch("/api/voos/9999/status", json={"status": "EMBARQUE"})

    assert resposta.status_code == 404
    assert resposta.json()["codigo"] == "NAO_ENCONTRADO"
