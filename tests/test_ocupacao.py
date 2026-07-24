"""A ocupação do voo é sempre derivada das reservas — nunca uma coluna no banco.

Cada teste aqui mexe no estado das reservas e confere que o número de assentos
ocupados acompanha, sem que nada precise ser recalculado manualmente.
"""

from tests.conftest import criar_aeronave, criar_passageiro, criar_reserva


def ocupacao(client, voo_id: int) -> dict:
    return client.get(f"/api/voos/{voo_id}/ocupacao").json()


def test_voo_novo_comeca_vazio(client, voo):
    atual = ocupacao(client, voo["id"])

    assert atual == {
        "capacidade": 6,
        "ocupados": 0,
        "disponiveis": 6,
        "taxa_ocupacao": 0.0,
    }


def test_reserva_confirmada_ocupa_assento(client, voo, passageiro):
    criar_reserva(client, passageiro["id"], voo["id"])

    atual = ocupacao(client, voo["id"])

    assert atual["ocupados"] == 1
    assert atual["disponiveis"] == 5
    assert atual["taxa_ocupacao"] == 16.7


def test_check_in_nao_muda_a_ocupacao(client, voo, reserva):
    client.patch(f"/api/reservas/{reserva['id']}/check-in")

    assert ocupacao(client, voo["id"])["ocupados"] == 1


def test_cancelar_devolve_o_assento(client, voo, reserva):
    client.delete(f"/api/reservas/{reserva['id']}")

    assert ocupacao(client, voo["id"])["ocupados"] == 0


def test_no_show_devolve_o_assento(client, voo, reserva):
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "EMBARQUE"})
    client.patch(f"/api/reservas/{reserva['id']}/no-show")

    assert ocupacao(client, voo["id"])["ocupados"] == 0


def test_passageiro_embarcado_continua_ocupando(client, voo, reserva):
    client.patch(f"/api/reservas/{reserva['id']}/check-in")
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "EMBARQUE"})
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "FINALIZADO"})

    assert ocupacao(client, voo["id"])["ocupados"] == 1


def test_cancelar_o_voo_zera_a_ocupacao(client, voo, reserva):
    client.patch(f"/api/voos/{voo['id']}/status", json={"status": "CANCELADO"})

    assert ocupacao(client, voo["id"])["ocupados"] == 0


def test_voo_lotado_chega_a_cem_por_cento(client, voo):
    for indice in range(6):
        p = criar_passageiro(client, f"Passageiro {indice}", f"DOC-{indice}")
        criar_reserva(client, p["id"], voo["id"])

    atual = ocupacao(client, voo["id"])

    assert atual["ocupados"] == 6
    assert atual["disponiveis"] == 0
    assert atual["taxa_ocupacao"] == 100.0


def test_a_capacidade_vem_da_aeronave(client, voo, terminal):
    maior = criar_aeronave(client, prefixo="ZS-BIG", capacidade=180)

    client.put(f"/api/voos/{voo['id']}", json={"aeronave_id": maior["id"]})

    assert ocupacao(client, voo["id"])["capacidade"] == 180


def test_trocar_por_aeronave_menor_que_os_confirmados_devolve_409(client, voo):
    for indice in range(3):
        p = criar_passageiro(client, f"Passageiro {indice}", f"DOC-{indice}")
        criar_reserva(client, p["id"], voo["id"])
    pequena = criar_aeronave(client, prefixo="ZS-SML", capacidade=2)

    resposta = client.put(f"/api/voos/{voo['id']}", json={"aeronave_id": pequena["id"]})

    assert resposta.status_code == 409
    assert "menos que os 3 passageiros" in resposta.json()["detail"]


def test_a_ocupacao_aparece_na_listagem_de_voos(client, voo, reserva):
    voos = client.get("/api/voos").json()

    assert voos[0]["ocupacao"]["ocupados"] == 1


def test_manifesto_lista_os_passageiros_do_voo(client, voo, passageiro, reserva):
    manifesto = client.get(f"/api/voos/{voo['id']}/passageiros").json()

    assert len(manifesto) == 1
    assert manifesto[0]["passageiro"]["nome"] == passageiro["nome"]


def test_nao_remove_voo_com_passageiros_confirmados(client, voo, reserva):
    resposta = client.delete(f"/api/voos/{voo['id']}")

    assert resposta.status_code == 422
    assert "Cancele o voo" in resposta.json()["detail"]


def test_dashboard_consolida_a_ocupacao_dos_voos_ativos(client, voo, reserva):
    resumo = client.get("/api/dashboard/resumo").json()

    assert resumo["total_voos"] == 1
    assert resumo["voos_por_status"]["NO_HORARIO"] == 1
    assert resumo["taxa_ocupacao_media"] == 16.7
    assert resumo["total_passageiros"] == 1
