from datetime import datetime

from pydantic import BaseModel

from src.entities.base import Esquema
from src.entities.vaga import VagaResumo
from src.entities.voo import VooResumo
from src.utils.enums import FinalidadeAlocacao


class AlocacaoCriar(BaseModel):
    vaga_id: int
    inicio: datetime | None = None
    fim: datetime | None = None
    finalidade: FinalidadeAlocacao = FinalidadeAlocacao.DESEMBARQUE


class AlocacaoResposta(Esquema):
    id: int
    voo_id: int
    vaga_id: int
    inicio: datetime
    fim: datetime | None = None
    finalidade: FinalidadeAlocacao
    ativa: bool
    vaga: VagaResumo | None = None
    voo: VooResumo | None = None
