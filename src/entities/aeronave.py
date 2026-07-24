from datetime import datetime

from pydantic import BaseModel, Field

from src.entities.base import Esquema


class AeronaveCriar(BaseModel):
    prefixo: str = Field(min_length=3, max_length=10)
    modelo: str = Field(min_length=2, max_length=60)
    companhia: str = Field(min_length=2, max_length=60)
    capacidade: int = Field(gt=0, le=1000)


class AeronaveAtualizar(BaseModel):
    prefixo: str | None = Field(default=None, min_length=3, max_length=10)
    modelo: str | None = Field(default=None, min_length=2, max_length=60)
    companhia: str | None = Field(default=None, min_length=2, max_length=60)
    capacidade: int | None = Field(default=None, gt=0, le=1000)


class AeronaveResumo(Esquema):
    id: int
    prefixo: str
    modelo: str
    companhia: str
    capacidade: int


class AeronaveResposta(AeronaveResumo):
    criado_em: datetime
    total_voos: int = 0
