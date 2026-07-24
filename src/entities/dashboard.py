from pydantic import BaseModel

from src.entities.voo import VooResposta


class ResumoDashboard(BaseModel):
    total_voos: int
    voos_por_status: dict[str, int]
    total_aeronaves: int
    total_passageiros: int
    vagas_livres: int
    vagas_ocupadas: int
    total_vagas: int
    taxa_ocupacao_media: float
    check_ins_hoje: int
    bagagens_por_status: dict[str, int]
    bagagens_extraviadas: int
    proximos_voos: list[VooResposta] = []
