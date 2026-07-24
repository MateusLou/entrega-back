from datetime import datetime

from pydantic import BaseModel, Field

from src.entities.base import Esquema
from src.utils.enums import TipoTerminal


class TerminalCriar(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    tipo: TipoTerminal


class TerminalAtualizar(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=80)
    tipo: TipoTerminal | None = None


class TerminalResumo(Esquema):
    id: int
    nome: str
    tipo: TipoTerminal


class TerminalResposta(TerminalResumo):
    criado_em: datetime
    total_vagas: int = 0
    vagas_livres: int = 0
