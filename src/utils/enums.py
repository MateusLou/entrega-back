"""Enums compartilhados entre models, entities e use cases."""

from enum import Enum


class TipoTerminal(str, Enum):
    NACIONAL = "NACIONAL"
    INTERNACIONAL = "INTERNACIONAL"


class TipoVaga(str, Enum):
    GATE = "GATE"
    REMOTA = "REMOTA"


class StatusVaga(str, Enum):
    LIVRE = "LIVRE"
    OCUPADA = "OCUPADA"
    MANUTENCAO = "MANUTENCAO"


class StatusVoo(str, Enum):
    NO_HORARIO = "NO_HORARIO"
    ATRASADO = "ATRASADO"
    EMBARQUE = "EMBARQUE"
    FINALIZADO = "FINALIZADO"
    CANCELADO = "CANCELADO"


class FinalidadeAlocacao(str, Enum):
    DESEMBARQUE = "DESEMBARQUE"
    EMBARQUE = "EMBARQUE"
    ABASTECIMENTO = "ABASTECIMENTO"
    PERNOITE = "PERNOITE"


class StatusReserva(str, Enum):
    CONFIRMADA = "CONFIRMADA"
    CHECK_IN_FEITO = "CHECK_IN_FEITO"
    EMBARCADA = "EMBARCADA"
    NO_SHOW = "NO_SHOW"
    REALOCADA = "REALOCADA"
    CANCELADA = "CANCELADA"


class StatusBagagem(str, Enum):
    DESPACHADA = "DESPACHADA"
    EM_TRIAGEM = "EM_TRIAGEM"
    CARREGADA = "CARREGADA"
    EXTRAVIADA = "EXTRAVIADA"
    ENTREGUE = "ENTREGUE"


class SentidoVoo(str, Enum):
    """Usado apenas como filtro de listagem de voos."""

    CHEGADA = "chegada"
    PARTIDA = "partida"


# --- Regras de transição -----------------------------------------------------

TRANSICOES_VOO: dict[StatusVoo, set[StatusVoo]] = {
    StatusVoo.NO_HORARIO: {StatusVoo.ATRASADO, StatusVoo.EMBARQUE, StatusVoo.CANCELADO},
    StatusVoo.ATRASADO: {StatusVoo.EMBARQUE, StatusVoo.CANCELADO},
    StatusVoo.EMBARQUE: {StatusVoo.FINALIZADO, StatusVoo.CANCELADO},
    StatusVoo.FINALIZADO: set(),
    StatusVoo.CANCELADO: set(),
}

TRANSICOES_BAGAGEM: dict[StatusBagagem, set[StatusBagagem]] = {
    StatusBagagem.DESPACHADA: {StatusBagagem.EM_TRIAGEM, StatusBagagem.EXTRAVIADA},
    StatusBagagem.EM_TRIAGEM: {StatusBagagem.CARREGADA, StatusBagagem.EXTRAVIADA},
    StatusBagagem.CARREGADA: {StatusBagagem.ENTREGUE, StatusBagagem.EXTRAVIADA},
    StatusBagagem.EXTRAVIADA: {StatusBagagem.EM_TRIAGEM, StatusBagagem.ENTREGUE},
    StatusBagagem.ENTREGUE: set(),
}

#: Reservas que efetivamente ocupam um assento da aeronave.
STATUS_RESERVA_OCUPANDO_ASSENTO: set[StatusReserva] = {
    StatusReserva.CONFIRMADA,
    StatusReserva.CHECK_IN_FEITO,
    StatusReserva.EMBARCADA,
}

#: Voos que ainda aceitam novas reservas.
STATUS_VOO_ACEITA_RESERVA: set[StatusVoo] = {StatusVoo.NO_HORARIO, StatusVoo.ATRASADO}

#: Voos que ainda não foram encerrados.
STATUS_VOO_ATIVO: set[StatusVoo] = {
    StatusVoo.NO_HORARIO,
    StatusVoo.ATRASADO,
    StatusVoo.EMBARQUE,
}
