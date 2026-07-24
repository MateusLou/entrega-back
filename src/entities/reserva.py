from datetime import datetime

from pydantic import BaseModel, Field

from src.entities.base import Esquema
from src.entities.passageiro import PassageiroResumo
from src.entities.voo import VooResumo
from src.utils.enums import StatusReserva


class ReservaCriar(BaseModel):
    passageiro_id: int
    voo_id: int
    assento: str | None = Field(default=None, max_length=5)


class RealocarReserva(BaseModel):
    voo_destino_id: int
    assento: str | None = Field(default=None, max_length=5)


class ReservaResposta(Esquema):
    id: int
    passageiro_id: int
    voo_id: int
    assento: str | None = None
    status: StatusReserva
    check_in_em: datetime | None = None
    reserva_origem_id: int | None = None
    criado_em: datetime
    passageiro: PassageiroResumo | None = None
    voo: VooResumo | None = None
    total_bagagens: int = 0
