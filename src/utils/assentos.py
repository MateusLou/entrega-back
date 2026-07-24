"""Geração de assentos a partir da capacidade da aeronave.

Modelo simplificado: fileiras de 6 assentos (A-F), numeradas a partir de 1.
"""

COLUNAS = "ABCDEF"


def gerar_assentos(capacidade: int) -> list[str]:
    assentos: list[str] = []
    fileira = 1
    while len(assentos) < capacidade:
        for coluna in COLUNAS:
            if len(assentos) >= capacidade:
                break
            assentos.append(f"{fileira}{coluna}")
        fileira += 1
    return assentos


def proximo_assento_livre(capacidade: int, ocupados: set[str]) -> str | None:
    for assento in gerar_assentos(capacidade):
        if assento not in ocupados:
            return assento
    return None


def assento_valido(capacidade: int, assento: str) -> bool:
    return assento.upper() in set(gerar_assentos(capacidade))
