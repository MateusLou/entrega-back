"""Realocação de passageiro: o fluxo de "imprevisto" descrito no enunciado.

Quem perde o voo (ou tem o voo cancelado) é movido para outro voo com o mesmo destino,
e as malas despachadas acompanham o passageiro.
"""

import pytest

from tests.conftest import criar_passageiro, criar_reserva, criar_voo


@pytest.fixture
def voo_alternativo(client, aeronave, terminal):
    """Outro voo para o mesmo destino do voo da fixture `voo` (CPT -> JNB)."""
    return criar_voo(
        client, aeronave["id"], terminal["id"], codigo="TS900", horas_ate_partida=8
    )


def perder_o_voo(client, voo_id: int, reserva_id: int) -> None:
    client.patch(f"/api/voos/{voo_id}/status", json={"status": "EMBARQUE"})
    resposta = client.patch(f"/api/reservas/{reserva_id}/no-show")
    assert resposta.status_code == 200, resposta.text


def test_realoca_passageiro_que_perdeu_o_voo(client, voo, reserva, voo_alternativo):
    perder_o_voo(client, voo["id"], reserva["id"])

    resposta = client.post(
        f"/api/reservas/{reserva['id']}/realocar",
        json={"voo_destino_id": voo_alternativo["id"]},
    )

    assert resposta.status_code == 200, resposta.text
    nova = resposta.json()
    assert nova["voo_id"] == voo_alternativo["id"]
    assert nova["status"] == "CONFIRMADA"
    assert nova["assento"] is not None
    # A nova reserva aponta para a que deu origem a ela.
    assert nova["reserva_origem_id"] == reserva["id"]


def test_reserva_de_origem_vira_realocada(client, voo, reserva, voo_alternativo):
    perder_o_voo(client, voo["id"], reserva["id"])

    client.post(
        f"/api/reservas/{reserva['id']}/realocar",
        json={"voo_destino_id": voo_alternativo["id"]},
    )

    antiga = client.get(f"/api/reservas/{reserva['id']}").json()
    assert antiga["status"] == "REALOCADA"
    assert antiga["assento"] is None


def test_as_malas_acompanham_o_passageiro(client, voo, reserva, voo_alternativo):
    mala = client.post(
        "/api/bagagens", json={"reserva_id": reserva["id"], "peso_kg": 18.5}
    ).json()
    perder_o_voo(client, voo["id"], reserva["id"])

    nova = client.post(
        f"/api/reservas/{reserva['id']}/realocar",
        json={"voo_destino_id": voo_alternativo["id"]},
    ).json()

    malas_da_nova = client.get(f"/api/reservas/{nova['id']}/bagagens").json()
    assert [m["id"] for m in malas_da_nova] == [mala["id"]]
    assert client.get(f"/api/reservas/{reserva['id']}/bagagens").json() == []
    # E a mala agora aparece no manifesto de bagagens do novo voo.
    bagagens_do_voo = client.get(f"/api/voos/{voo_alternativo['id']}/bagagens").json()
    assert [b["id"] for b in bagagens_do_voo] == [mala["id"]]


def test_realocar_reserva_confirmada_devolve_409(client, reserva, voo_alternativo):
    resposta = client.post(
        f"/api/reservas/{reserva['id']}/realocar",
        json={"voo_destino_id": voo_alternativo["id"]},
    )

    assert resposta.status_code == 409
    assert "NO_SHOW" in resposta.json()["detail"]


def test_voo_cancelado_tambem_permite_realocar(client, voo, reserva, voo_alternativo):
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "CANCELADO"})

    resposta = client.post(
        f"/api/reservas/{reserva['id']}/realocar",
        json={"voo_destino_id": voo_alternativo["id"]},
    )

    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["voo_id"] == voo_alternativo["id"]


def test_destino_diferente_devolve_422(client, voo, reserva, aeronave, terminal):
    outro_destino = criar_voo(
        client, aeronave["id"], terminal["id"], codigo="TS800", destino="DUR"
    )
    perder_o_voo(client, voo["id"], reserva["id"])

    resposta = client.post(
        f"/api/reservas/{reserva['id']}/realocar",
        json={"voo_destino_id": outro_destino["id"]},
    )

    assert resposta.status_code == 422
    assert "DUR" in resposta.json()["detail"]


def test_realocar_para_o_mesmo_voo_devolve_422(client, voo, reserva):
    perder_o_voo(client, voo["id"], reserva["id"])

    resposta = client.post(
        f"/api/reservas/{reserva['id']}/realocar", json={"voo_destino_id": voo["id"]}
    )

    assert resposta.status_code == 422
    assert "diferente" in resposta.json()["detail"]


def test_voo_destino_ja_partido_devolve_422(client, voo, reserva, aeronave, terminal):
    passado = criar_voo(
        client, aeronave["id"], terminal["id"], codigo="TS700", horas_ate_partida=-5
    )
    perder_o_voo(client, voo["id"], reserva["id"])

    resposta = client.post(
        f"/api/reservas/{reserva['id']}/realocar", json={"voo_destino_id": passado["id"]}
    )

    assert resposta.status_code == 422
    assert "já partiu" in resposta.json()["detail"]


def test_voo_destino_lotado_devolve_409(client, voo, reserva, voo_alternativo):
    for indice in range(6):  # capacidade da aeronave de teste
        p = criar_passageiro(client, f"Lotacao {indice}", f"LOT-{indice}")
        criar_reserva(client, p["id"], voo_alternativo["id"])
    perder_o_voo(client, voo["id"], reserva["id"])

    resposta = client.post(
        f"/api/reservas/{reserva['id']}/realocar",
        json={"voo_destino_id": voo_alternativo["id"]},
    )

    assert resposta.status_code == 409
    assert "lotado" in resposta.json()["detail"]


def test_voo_destino_em_embarque_devolve_409(client, voo, reserva, voo_alternativo):
    perder_o_voo(client, voo["id"], reserva["id"])
    client.patch(f"/api/voos/{voo_alternativo['id']}/status", json={"status": "EMBARQUE"})

    resposta = client.post(
        f"/api/reservas/{reserva['id']}/realocar",
        json={"voo_destino_id": voo_alternativo["id"]},
    )

    assert resposta.status_code == 409


def test_assento_pode_ser_escolhido_na_realocacao(client, voo, reserva, voo_alternativo):
    perder_o_voo(client, voo["id"], reserva["id"])

    resposta = client.post(
        f"/api/reservas/{reserva['id']}/realocar",
        json={"voo_destino_id": voo_alternativo["id"], "assento": "1E"},
    )

    assert resposta.json()["assento"] == "1E"


def test_ocupacao_migra_de_um_voo_para_o_outro(client, voo, reserva, voo_alternativo):
    perder_o_voo(client, voo["id"], reserva["id"])

    client.post(
        f"/api/reservas/{reserva['id']}/realocar",
        json={"voo_destino_id": voo_alternativo["id"]},
    )

    assert client.get(f"/api/voos/{voo['id']}/ocupacao").json()["ocupados"] == 0
    assert client.get(f"/api/voos/{voo_alternativo['id']}/ocupacao").json()["ocupados"] == 1
