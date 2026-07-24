"""Ocupação do pátio: vagas/gates, alocação de aeronave e liberação da posição."""

from datetime import timedelta

from tests.conftest import AGORA, criar_terminal, criar_vaga, criar_voo


def test_alocar_ocupa_a_vaga(client, voo, terminal):
    vaga = criar_vaga(client, terminal["id"])

    resposta = client.post(
        f"/api/voos/{voo['id']}/alocacoes",
        json={"vaga_id": vaga["id"], "finalidade": "EMBARQUE"},
    )

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["ativa"] is True
    assert resposta.json()["finalidade"] == "EMBARQUE"
    assert client.get(f"/api/vagas/{vaga['id']}").json()["status"] == "OCUPADA"


def test_vaga_ocupada_mostra_o_voo_atual(client, voo, terminal):
    vaga = criar_vaga(client, terminal["id"])
    client.post(f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga["id"]})

    assert client.get(f"/api/vagas/{vaga['id']}").json()["voo_atual"] == voo["codigo"]
    assert client.get(f"/api/voos/{voo['id']}").json()["vaga_atual"]["codigo"] == "A1"


def test_vaga_de_outro_terminal_devolve_422(client, voo, aeronave):
    outro = criar_terminal(client, nome="Terminal Internacional", tipo="INTERNACIONAL")
    vaga_de_fora = criar_vaga(client, outro["id"], codigo="B1")

    resposta = client.post(
        f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga_de_fora["id"]}
    )

    assert resposta.status_code == 422
    assert "mesmo terminal" in resposta.json()["detail"]


def test_vaga_em_manutencao_devolve_409(client, voo, terminal):
    vaga = criar_vaga(client, terminal["id"])
    client.put(f"/api/vagas/{vaga['id']}", json={"status": "MANUTENCAO"})

    resposta = client.post(
        f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga["id"]}
    )

    assert resposta.status_code == 409
    assert "manutenção" in resposta.json()["detail"]


def test_dois_voos_na_mesma_vaga_no_mesmo_periodo_devolve_409(
    client, voo, terminal, aeronave
):
    vaga = criar_vaga(client, terminal["id"])
    client.post(f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga["id"]})
    concorrente = criar_voo(client, aeronave["id"], terminal["id"], codigo="TS300")

    resposta = client.post(
        f"/api/voos/{concorrente['id']}/alocacoes", json={"vaga_id": vaga["id"]}
    )

    assert resposta.status_code == 409
    assert "já está ocupada" in resposta.json()["detail"]


def test_periodos_que_nao_se_sobrepoem_sao_aceitos(client, voo, terminal, aeronave):
    vaga = criar_vaga(client, terminal["id"])
    manha_inicio = AGORA
    manha_fim = AGORA + timedelta(hours=1)
    client.post(
        f"/api/voos/{voo['id']}/alocacoes",
        json={
            "vaga_id": vaga["id"],
            "inicio": manha_inicio.isoformat(),
            "fim": manha_fim.isoformat(),
        },
    )
    seguinte = criar_voo(client, aeronave["id"], terminal["id"], codigo="TS400")

    resposta = client.post(
        f"/api/voos/{seguinte['id']}/alocacoes",
        json={
            "vaga_id": vaga["id"],
            "inicio": (manha_fim + timedelta(minutes=30)).isoformat(),
        },
    )

    assert resposta.status_code == 201, resposta.text


def test_voo_nao_pode_ocupar_duas_vagas(client, voo, terminal):
    primeira = criar_vaga(client, terminal["id"], codigo="A1")
    segunda = criar_vaga(client, terminal["id"], codigo="A2")
    client.post(f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": primeira["id"]})

    resposta = client.post(
        f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": segunda["id"]}
    )

    assert resposta.status_code == 409
    assert "já ocupa uma vaga" in resposta.json()["detail"]


def test_liberar_devolve_a_vaga_e_encerra_a_alocacao(client, voo, terminal):
    vaga = criar_vaga(client, terminal["id"])
    alocacao = client.post(
        f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga["id"]}
    ).json()

    resposta = client.patch(
        f"/api/voos/{voo['id']}/alocacoes/{alocacao['id']}/liberar"
    )

    assert resposta.status_code == 200
    assert resposta.json()["ativa"] is False
    assert resposta.json()["fim"] is not None
    assert client.get(f"/api/vagas/{vaga['id']}").json()["status"] == "LIVRE"


def test_liberar_duas_vezes_devolve_409(client, voo, terminal):
    vaga = criar_vaga(client, terminal["id"])
    alocacao = client.post(
        f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga["id"]}
    ).json()
    client.patch(f"/api/voos/{voo['id']}/alocacoes/{alocacao['id']}/liberar")

    resposta = client.patch(f"/api/voos/{voo['id']}/alocacoes/{alocacao['id']}/liberar")

    assert resposta.status_code == 409
    assert "já foi liberada" in resposta.json()["detail"]


def test_a_vaga_pode_ser_reutilizada_depois_de_liberada(client, voo, terminal, aeronave):
    vaga = criar_vaga(client, terminal["id"])
    alocacao = client.post(
        f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga["id"]}
    ).json()
    client.patch(f"/api/voos/{voo['id']}/alocacoes/{alocacao['id']}/liberar")
    seguinte = criar_voo(client, aeronave["id"], terminal["id"], codigo="TS500")

    resposta = client.post(
        f"/api/voos/{seguinte['id']}/alocacoes", json={"vaga_id": vaga["id"]}
    )

    assert resposta.status_code == 201, resposta.text


def test_o_historico_de_alocacoes_e_preservado(client, voo, terminal):
    vaga = criar_vaga(client, terminal["id"])
    alocacao = client.post(
        f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga["id"]}
    ).json()
    client.patch(f"/api/voos/{voo['id']}/alocacoes/{alocacao['id']}/liberar")
    client.post(f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga["id"]})

    historico = client.get(f"/api/voos/{voo['id']}/alocacoes").json()

    assert len(historico) == 2
    assert [a["ativa"] for a in historico].count(True) == 1


def test_voo_finalizado_nao_recebe_vaga(client, voo, terminal):
    vaga = criar_vaga(client, terminal["id"])
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "EMBARQUE"})
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "FINALIZADO"})

    resposta = client.post(
        f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga["id"]}
    )

    assert resposta.status_code == 409


def test_fim_anterior_ao_inicio_devolve_422(client, voo, terminal):
    vaga = criar_vaga(client, terminal["id"])

    resposta = client.post(
        f"/api/voos/{voo['id']}/alocacoes",
        json={
            "vaga_id": vaga["id"],
            "inicio": AGORA.isoformat(),
            "fim": (AGORA - timedelta(hours=1)).isoformat(),
        },
    )

    assert resposta.status_code == 422


def test_nao_remove_vaga_com_alocacao_ativa(client, voo, terminal):
    vaga = criar_vaga(client, terminal["id"])
    client.post(f"/api/voos/{voo['id']}/alocacoes", json={"vaga_id": vaga["id"]})

    resposta = client.delete(f"/api/vagas/{vaga['id']}")

    assert resposta.status_code == 422
    assert "alocação ativa" in resposta.json()["detail"]


# --- Unicidade do código da vaga ---------------------------------------------


def test_cada_terminal_tem_o_seu_proprio_gate_a1(client, terminal):
    """O código só precisa ser único dentro do terminal (uq_vaga_terminal_codigo)."""
    internacional = criar_terminal(client, nome="Terminal Intl.", tipo="INTERNACIONAL")

    criar_vaga(client, terminal["id"], codigo="A1")
    resposta = client.post(
        "/api/vagas", json={"codigo": "A1", "terminal_id": internacional["id"]}
    )

    assert resposta.status_code == 201, resposta.text


def test_codigo_repetido_no_mesmo_terminal_devolve_409(client, terminal):
    criar_vaga(client, terminal["id"], codigo="A1")

    resposta = client.post(
        "/api/vagas", json={"codigo": "A1", "terminal_id": terminal["id"]}
    )

    assert resposta.status_code == 409
    assert "A1" in resposta.json()["detail"]


def test_mover_vaga_para_terminal_que_ja_tem_o_codigo_devolve_409(client, terminal):
    internacional = criar_terminal(client, nome="Terminal Intl.", tipo="INTERNACIONAL")
    criar_vaga(client, terminal["id"], codigo="A1")
    a_mover = criar_vaga(client, internacional["id"], codigo="B9")

    resposta = client.put(
        f"/api/vagas/{a_mover['id']}",
        json={"codigo": "A1", "terminal_id": terminal["id"]},
    )

    assert resposta.status_code == 409
