"""Logística de bagagens: despacho, fluxo de status e rastreio pela etiqueta."""

import pytest

from tests.conftest import criar_passageiro, criar_reserva


def despachar(client, reserva_id: int, **campos) -> dict:
    resposta = client.post("/api/bagagens", json={"reserva_id": reserva_id, **campos})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def mover(client, bagagem_id: int, status: str, **campos):
    return client.patch(
        f"/api/bagagens/{bagagem_id}/status", json={"status": status, **campos}
    )


def test_despachar_gera_etiqueta_e_local_inicial(client, reserva):
    bagagem = despachar(client, reserva["id"], peso_kg=23.4)

    assert bagagem["etiqueta"] == "CPT000001"
    assert bagagem["status"] == "DESPACHADA"
    assert bagagem["local_atual"] == "Balcão de check-in"
    assert float(bagagem["peso_kg"]) == 23.4


def test_etiquetas_nao_se_repetem(client, voo, passageiro):
    primeira = despachar(client, criar_reserva(client, passageiro["id"], voo["id"])["id"])
    outro = criar_passageiro(client, "Outro", "DOC-2")
    segunda = despachar(client, criar_reserva(client, outro["id"], voo["id"])["id"])

    assert primeira["etiqueta"] != segunda["etiqueta"]


def test_etiqueta_duplicada_devolve_409(client, reserva):
    despachar(client, reserva["id"], etiqueta="MALA-1")

    resposta = client.post(
        "/api/bagagens", json={"reserva_id": reserva["id"], "etiqueta": "mala-1"}
    )

    assert resposta.status_code == 409


def test_a_mala_tem_um_dono_e_um_voo(client, reserva, passageiro, voo):
    bagagem = despachar(client, reserva["id"])

    assert bagagem["passageiro"]["id"] == passageiro["id"]
    assert bagagem["voo"]["id"] == voo["id"]


def test_passageiro_pode_despachar_varias_malas(client, reserva, passageiro):
    despachar(client, reserva["id"])
    despachar(client, reserva["id"])

    malas = client.get(f"/api/passageiros/{passageiro['id']}/bagagens").json()

    assert len(malas) == 2


def test_nao_despacha_em_reserva_cancelada(client, reserva):
    client.delete(f"/api/reservas/{reserva['id']}")

    resposta = client.post("/api/bagagens", json={"reserva_id": reserva["id"]})

    assert resposta.status_code == 409
    assert "reserva ativa" in resposta.json()["detail"]


def test_fluxo_completo_ate_a_entrega(client, reserva):
    bagagem = despachar(client, reserva["id"])

    for status in ("EM_TRIAGEM", "CARREGADA", "ENTREGUE"):
        resposta = mover(client, bagagem["id"], status)
        assert resposta.status_code == 200, resposta.text
        assert resposta.json()["status"] == status


def test_pular_etapa_do_fluxo_devolve_409(client, reserva):
    bagagem = despachar(client, reserva["id"])

    resposta = mover(client, bagagem["id"], "ENTREGUE")

    assert resposta.status_code == 409
    assert "Transição inválida" in resposta.json()["detail"]


@pytest.mark.parametrize("de", ["DESPACHADA", "EM_TRIAGEM", "CARREGADA"])
def test_extravio_e_alcancavel_de_qualquer_estado_nao_final(client, reserva, de):
    bagagem = despachar(client, reserva["id"])
    for passo in {"EM_TRIAGEM": ["EM_TRIAGEM"], "CARREGADA": ["EM_TRIAGEM", "CARREGADA"]}.get(de, []):
        mover(client, bagagem["id"], passo)

    resposta = mover(client, bagagem["id"], "EXTRAVIADA")

    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["status"] == "EXTRAVIADA"


def test_mala_extraviada_pode_voltar_para_a_triagem(client, reserva):
    bagagem = despachar(client, reserva["id"])
    mover(client, bagagem["id"], "EXTRAVIADA")

    resposta = mover(client, bagagem["id"], "EM_TRIAGEM")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "EM_TRIAGEM"


def test_entregue_e_estado_final(client, reserva):
    bagagem = despachar(client, reserva["id"])
    for status in ("EM_TRIAGEM", "CARREGADA", "ENTREGUE"):
        mover(client, bagagem["id"], status)

    resposta = mover(client, bagagem["id"], "EM_TRIAGEM")

    assert resposta.status_code == 409
    assert client.get(f"/api/bagagens/{bagagem['id']}").json()["transicoes_permitidas"] == []


def test_local_atual_pode_ser_atualizado_junto_com_o_status(client, reserva):
    bagagem = despachar(client, reserva["id"])

    resposta = mover(client, bagagem["id"], "EM_TRIAGEM", local_atual="Esteira 3")

    assert resposta.json()["local_atual"] == "Esteira 3"


def test_rastreio_pela_etiqueta(client, reserva):
    bagagem = despachar(client, reserva["id"], etiqueta="CPT999999")

    resposta = client.get("/api/bagagens/rastreio/CPT999999")

    assert resposta.status_code == 200
    assert resposta.json()["id"] == bagagem["id"]


def test_rastreio_de_etiqueta_inexistente_devolve_404(client):
    resposta = client.get("/api/bagagens/rastreio/NAO-EXISTE")

    assert resposta.status_code == 404


def test_nao_remove_mala_ja_carregada(client, reserva):
    bagagem = despachar(client, reserva["id"])
    mover(client, bagagem["id"], "EM_TRIAGEM")
    mover(client, bagagem["id"], "CARREGADA")

    resposta = client.delete(f"/api/bagagens/{bagagem['id']}")

    assert resposta.status_code == 422
    assert "carregada" in resposta.json()["detail"]


def test_filtrar_bagagens_por_status(client, voo, passageiro):
    reserva = criar_reserva(client, passageiro["id"], voo["id"])
    perdida = despachar(client, reserva["id"])
    despachar(client, reserva["id"])
    mover(client, perdida["id"], "EXTRAVIADA")

    extraviadas = client.get("/api/bagagens", params={"status": "EXTRAVIADA"}).json()

    assert [b["id"] for b in extraviadas] == [perdida["id"]]
