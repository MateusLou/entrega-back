"""Notificação do n8n a cada passageiro cadastrado.

O contrato tem três partes: avisar quando há webhook configurado, ficar quieto
quando não há, e nunca deixar uma falha do n8n atrapalhar o cadastro.
"""

from types import SimpleNamespace

import httpx
import pytest

from src.utils import notificacoes
from tests.conftest import criar_passageiro

URL_WEBHOOK = "https://exemplo.app.n8n.cloud/webhook/passageiro-novo"


def configurar_webhook(monkeypatch, url: str | None) -> None:
    """Troca o get_settings do módulo — mais limpo que mexer no lru_cache dele."""
    monkeypatch.setattr(
        notificacoes, "get_settings", lambda: SimpleNamespace(N8N_WEBHOOK_URL=url)
    )


@pytest.fixture
def chamadas(monkeypatch) -> list[dict]:
    """Registra o que teria sido enviado, sem sair para a rede."""
    registradas: list[dict] = []

    def _post(url, json=None, timeout=None):
        registradas.append({"url": url, "json": json, "timeout": timeout})
        return httpx.Response(200)

    monkeypatch.setattr(httpx, "post", _post)
    return registradas


def test_sem_webhook_configurado_nao_notifica_ninguem(client, chamadas, monkeypatch):
    configurar_webhook(monkeypatch, None)

    criar_passageiro(client, "Ada Lovelace", "DOC-100")

    assert chamadas == []


def test_com_webhook_configurado_envia_o_passageiro(client, chamadas, monkeypatch):
    configurar_webhook(monkeypatch, URL_WEBHOOK)

    passageiro = criar_passageiro(client, "Thabo Mokoena", "DOC-101")

    assert len(chamadas) == 1
    enviado = chamadas[0]
    assert enviado["url"] == URL_WEBHOOK
    assert enviado["timeout"] == notificacoes.TIMEOUT_SEGUNDOS
    assert enviado["json"]["id"] == passageiro["id"]
    assert enviado["json"]["nome"] == "Thabo Mokoena"
    assert enviado["json"]["documento"] == "DOC-101"


def test_payload_vai_serializavel_em_json(client, chamadas, monkeypatch):
    """model_dump(mode="json") — sem isso o datetime de criado_em quebra o envio."""
    configurar_webhook(monkeypatch, URL_WEBHOOK)

    criar_passageiro(client, "Ana Célia", "DOC-102")

    assert isinstance(chamadas[0]["json"]["criado_em"], str)


def test_notificar_so_dispara_no_cadastro(client, chamadas, monkeypatch):
    configurar_webhook(monkeypatch, URL_WEBHOOK)
    passageiro = criar_passageiro(client, "Nomvula Dlamini", "DOC-103")
    chamadas.clear()

    client.put(
        f"/api/passageiros/{passageiro['id']}",
        json={"nome": "Nomvula Dlamini Silva"},
    )
    client.get("/api/passageiros")

    assert chamadas == []


def test_falha_do_webhook_nao_derruba_o_cadastro(client, monkeypatch):
    configurar_webhook(monkeypatch, URL_WEBHOOK)

    def _post_que_falha(url, json=None, timeout=None):
        raise httpx.ConnectError("n8n fora do ar")

    monkeypatch.setattr(httpx, "post", _post_que_falha)

    resposta = client.post(
        "/api/passageiros", json={"nome": "Sipho Carvalho", "documento": "DOC-104"}
    )

    assert resposta.status_code == 201, resposta.text
    documentos = [p["documento"] for p in client.get("/api/passageiros").json()]
    assert "DOC-104" in documentos
