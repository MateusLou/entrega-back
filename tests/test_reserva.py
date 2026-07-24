"""Vínculo passageiro <-> voo: criação da reserva, assentos, check-in e no-show."""

import pytest

from tests.conftest import criar_passageiro, criar_reserva


def test_reserva_recebe_o_primeiro_assento_livre(client, passageiro, voo):
    reserva = criar_reserva(client, passageiro["id"], voo["id"])

    assert reserva["status"] == "CONFIRMADA"
    assert reserva["assento"] == "1A"


def test_assentos_sao_distribuidos_em_sequencia(client, voo):
    assentos = []
    for indice in range(3):
        p = criar_passageiro(client, f"Passageiro {indice}", f"DOC-{indice}")
        assentos.append(criar_reserva(client, p["id"], voo["id"])["assento"])

    assert assentos == ["1A", "1B", "1C"]


def test_assento_pedido_e_respeitado(client, passageiro, voo):
    reserva = criar_reserva(client, passageiro["id"], voo["id"], assento="1d")

    assert reserva["assento"] == "1D"


def test_assento_ja_ocupado_devolve_409(client, voo, passageiro):
    criar_reserva(client, passageiro["id"], voo["id"], assento="1C")
    outro = criar_passageiro(client, "Outro", "DOC-999")

    resposta = client.post(
        "/api/reservas",
        json={"passageiro_id": outro["id"], "voo_id": voo["id"], "assento": "1C"},
    )

    assert resposta.status_code == 409
    assert "1C" in resposta.json()["detail"]


def test_assento_inexistente_na_aeronave_devolve_422(client, voo, passageiro):
    # A aeronave da fixture tem 6 lugares: vai de 1A a 1F.
    resposta = client.post(
        "/api/reservas",
        json={"passageiro_id": passageiro["id"], "voo_id": voo["id"], "assento": "30F"},
    )

    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "REGRA_DE_NEGOCIO"


def test_voo_lotado_recusa_nova_reserva(client, voo):
    # Capacidade 6: a sétima reserva não cabe.
    for indice in range(6):
        p = criar_passageiro(client, f"Passageiro {indice}", f"DOC-{indice}")
        criar_reserva(client, p["id"], voo["id"])
    excedente = criar_passageiro(client, "Excedente", "DOC-X")

    resposta = client.post(
        "/api/reservas",
        json={"passageiro_id": excedente["id"], "voo_id": voo["id"]},
    )

    assert resposta.status_code == 409
    assert "lotado" in resposta.json()["detail"]


@pytest.mark.parametrize("status_voo", ["EMBARQUE", "CANCELADO"])
def test_voo_que_nao_aceita_reserva_devolve_409(client, voo, passageiro, status_voo):
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": status_voo})

    resposta = client.post(
        "/api/reservas", json={"passageiro_id": passageiro["id"], "voo_id": voo["id"]}
    )

    assert resposta.status_code == 409
    assert "não aceita novas reservas" in resposta.json()["detail"]


def test_reserva_duplicada_no_mesmo_voo_devolve_409(client, passageiro, voo, reserva):
    resposta = client.post(
        "/api/reservas", json={"passageiro_id": passageiro["id"], "voo_id": voo["id"]}
    )

    assert resposta.status_code == 409
    assert "já possui uma reserva ativa" in resposta.json()["detail"]


def test_reservar_de_novo_apos_cancelar_reaproveita_a_linha(client, passageiro, voo, reserva):
    """A unique (passageiro_id, voo_id) impede duas linhas para o mesmo par."""
    client.delete(f"/api/reservas/{reserva['id']}")

    nova = criar_reserva(client, passageiro["id"], voo["id"])

    assert nova["id"] == reserva["id"]
    assert nova["status"] == "CONFIRMADA"
    assert nova["check_in_em"] is None


def test_passageiro_pode_estar_em_varios_voos(client, passageiro, voo, aeronave, terminal):
    from tests.conftest import criar_voo

    segundo = criar_voo(client, aeronave["id"], terminal["id"], codigo="TS200")
    criar_reserva(client, passageiro["id"], voo["id"])
    criar_reserva(client, passageiro["id"], segundo["id"])

    reservas = client.get(f"/api/passageiros/{passageiro['id']}/reservas").json()

    assert len(reservas) == 2
    assert {r["voo_id"] for r in reservas} == {voo["id"], segundo["id"]}


# --- Check-in ----------------------------------------------------------------


def test_check_in_marca_o_horario(client, reserva):
    resposta = client.patch(f"/api/reservas/{reserva['id']}/check-in")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "CHECK_IN_FEITO"
    assert resposta.json()["check_in_em"] is not None


def test_check_in_repetido_devolve_409(client, reserva):
    client.patch(f"/api/reservas/{reserva['id']}/check-in")

    resposta = client.patch(f"/api/reservas/{reserva['id']}/check-in")

    assert resposta.status_code == 409
    assert "já foi realizado" in resposta.json()["detail"]


def test_check_in_de_reserva_cancelada_devolve_409(client, reserva):
    client.delete(f"/api/reservas/{reserva['id']}")

    resposta = client.patch(f"/api/reservas/{reserva['id']}/check-in")

    assert resposta.status_code == 409
    assert "CONFIRMADA" in resposta.json()["detail"]


def test_check_in_em_voo_finalizado_devolve_409(client, voo, reserva):
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "EMBARQUE"})
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "FINALIZADO"})

    resposta = client.patch(f"/api/reservas/{reserva['id']}/check-in")

    assert resposta.status_code == 409


# --- No-show -----------------------------------------------------------------


def test_no_show_antes_do_embarque_devolve_409(client, reserva):
    resposta = client.patch(f"/api/reservas/{reserva['id']}/no-show")

    assert resposta.status_code == 409
    assert "depois que o voo entra em embarque" in resposta.json()["detail"]


def test_no_show_devolve_o_assento_ao_voo(client, voo, passageiro):
    reserva = criar_reserva(client, passageiro["id"], voo["id"], assento="1A")
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "EMBARQUE"})

    resposta = client.patch(f"/api/reservas/{reserva['id']}/no-show")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "NO_SHOW"
    assert resposta.json()["assento"] is None
    assert client.get(f"/api/voos/{voo['id']}/ocupacao").json()["ocupados"] == 0


def test_no_show_de_reserva_ja_encerrada_devolve_409(client, voo, reserva):
    client.delete(f"/api/reservas/{reserva['id']}")
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "EMBARQUE"})

    resposta = client.patch(f"/api/reservas/{reserva['id']}/no-show")

    assert resposta.status_code == 409


# --- Cancelamento ------------------------------------------------------------


def test_cancelar_libera_o_assento(client, reserva, voo):
    resposta = client.delete(f"/api/reservas/{reserva['id']}")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "CANCELADA"
    assert resposta.json()["assento"] is None


def test_nao_cancela_reserva_de_passageiro_embarcado(client, voo, reserva):
    client.patch(f"/api/reservas/{reserva['id']}/check-in")
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "EMBARQUE"})
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "FINALIZADO"})

    resposta = client.delete(f"/api/reservas/{reserva['id']}")

    assert resposta.status_code == 409
    assert "já embarcado" in resposta.json()["detail"]


def test_reserva_para_passageiro_inexistente_devolve_404(client, voo):
    resposta = client.post(
        "/api/reservas", json={"passageiro_id": 9999, "voo_id": voo["id"]}
    )

    assert resposta.status_code == 404
