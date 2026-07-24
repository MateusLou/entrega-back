from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.entities.base import Esquema
from src.entities.passageiro import PassageiroResumo
from src.entities.voo import VooResumo
from src.utils.enums import StatusBagagem


class BagagemCriar(BaseModel):
    reserva_id: int
    peso_kg: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    etiqueta: str | None = Field(default=None, max_length=20)
    local_atual: str | None = Field(default=None, max_length=80)


class BagagemAtualizarStatus(BaseModel):
    status: StatusBagagem
    local_atual: str | None = Field(default=None, max_length=80)


class BagagemResposta(Esquema):
    id: int
    etiqueta: str
    reserva_id: int
    peso_kg: Decimal
    status: StatusBagagem
    local_atual: str | None = None
    criado_em: datetime
    atualizado_em: datetime
    passageiro: PassageiroResumo | None = None
    voo: VooResumo | None = None
    transicoes_permitidas: list[StatusBagagem] = []
