"""Avisa sistemas externos sobre eventos do domínio.

Falha aqui nunca derruba a operação que originou o evento: quando estas funções
rodam, o cadastro já foi concluído e a resposta já saiu. Um n8n fora do ar vira
uma linha de log, não um erro para quem chamou a API.
"""

import logging

import httpx

from src.config.config import get_settings

logger = logging.getLogger(__name__)

#: Curto de propósito: o n8n fora do ar não pode segurar um worker da aplicação.
TIMEOUT_SEGUNDOS = 5.0


def notificar_passageiro_criado(passageiro: dict) -> None:
    """Envia o passageiro recém-cadastrado ao webhook do n8n, se configurado."""
    url = get_settings().N8N_WEBHOOK_URL
    if not url:
        return

    try:
        httpx.post(url, json=passageiro, timeout=TIMEOUT_SEGUNDOS)
    except httpx.HTTPError as erro:
        logger.warning(
            "Falha ao notificar o n8n sobre o passageiro %s: %s",
            passageiro.get("id"),
            erro,
        )
