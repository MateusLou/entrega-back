from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.entities.aeronave import AeronaveResumo
from src.entities.base import Esquema
from src.entities.terminal import TerminalResumo
from src.entities.vaga import VagaResumo
from src.utils.enums import StatusVoo


class VooCriar(BaseModel):
    codigo: str = Field(min_length=3, max_length=10)
    origem: str = Field(min_length=3, max_length=3)
    destino: str = Field(min_length=3, max_length=3)
    partida_prevista: datetime
    chegada_prevista: datetime
    aeronave_id: int
    terminal_id: int
    status: StatusVoo = StatusVoo.NO_HORARIO

    @field_validator("origem", "destino")
    @classmethod
    def _iata_maiusculo(cls, v: str) -> str:
        return v.upper()

    @field_validator("codigo")
    @classmethod
    def _codigo_maiusculo(cls, v: str) -> str:
        return v.upper()


class VooAtualizar(BaseModel):
    codigo: str | None = Field(default=None, min_length=3, max_length=10)
    origem: str | None = Field(default=None, min_length=3, max_length=3)
    destino: str | None = Field(default=None, min_length=3, max_length=3)
    partida_prevista: datetime | None = None
    chegada_prevista: datetime | None = None
    partida_real: datetime | None = None
    chegada_real: datetime | None = None
    aeronave_id: int | None = None
    terminal_id: int | None = None


class AlterarStatusVoo(BaseModel):
    status: StatusVoo


class OcupacaoVoo(BaseModel):
    capacidade: int
    ocupados: int
    disponiveis: int
    taxa_ocupacao: float = 0.0


class VooResumo(Esquema):
    id: int
    codigo: str
    origem: str
    destino: str
    partida_prevista: datetime
    chegada_prevista: datetime
    status: StatusVoo


class VooResposta(VooResumo):
    partida_real: datetime | None = None
    chegada_real: datetime | None = None
    aeronave_id: int
    terminal_id: int
    criado_em: datetime
    aeronave: AeronaveResumo | None = None
    terminal: TerminalResumo | None = None
    ocupacao: OcupacaoVoo | None = None
    vaga_atual: VagaResumo | None = None
    transicoes_permitidas: list[StatusVoo] = []
