from datetime import datetime

from pydantic import BaseModel, Field

from src.entities.base import Esquema
from src.entities.terminal import TerminalResumo
from src.utils.enums import StatusVaga, TipoVaga


class VagaCriar(BaseModel):
    codigo: str = Field(min_length=1, max_length=10)
    terminal_id: int
    tipo: TipoVaga = TipoVaga.GATE
    status: StatusVaga = StatusVaga.LIVRE


class VagaAtualizar(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=10)
    terminal_id: int | None = None
    tipo: TipoVaga | None = None
    status: StatusVaga | None = None


class VagaResumo(Esquema):
    id: int
    codigo: str
    tipo: TipoVaga
    status: StatusVaga


class VagaResposta(VagaResumo):
    terminal_id: int
    criado_em: datetime
    terminal: TerminalResumo | None = None
    voo_atual: str | None = None
