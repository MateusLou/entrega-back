from datetime import date

from sqlalchemy.orm import Session

from src.entities.dashboard import ResumoDashboard
from src.repositories.aeronave_repository import AeronaveRepository
from src.repositories.bagagem_repository import BagagemRepository
from src.repositories.passageiro_repository import PassageiroRepository
from src.repositories.reserva_repository import ReservaRepository
from src.repositories.vaga_repository import VagaRepository
from src.repositories.voo_repository import VooRepository
from src.use_cases.voo_use_case import VooUseCase
from src.utils.enums import StatusBagagem, StatusVaga


class DashboardUseCase:
    """Consolida os indicadores operacionais exibidos na tela inicial."""

    def __init__(self, db: Session):
        self.db = db
        self.voo_repo = VooRepository(db)
        self.vaga_repo = VagaRepository(db)
        self.aeronave_repo = AeronaveRepository(db)
        self.passageiro_repo = PassageiroRepository(db)
        self.reserva_repo = ReservaRepository(db)
        self.bagagem_repo = BagagemRepository(db)
        self.voo_use_case = VooUseCase(db)

    def resumo(self) -> ResumoDashboard:
        vagas = self.vaga_repo.listar()
        livres = sum(1 for v in vagas if v.status is StatusVaga.LIVRE)
        ocupadas = sum(1 for v in vagas if v.status is StatusVaga.OCUPADA)

        voos_ativos = self.voo_repo.listar_ativos()
        ocupados = self.reserva_repo.contar_ocupados_em_lote([v.id for v in voos_ativos])
        capacidade_total = sum(v.aeronave.capacidade for v in voos_ativos)
        ocupados_total = sum(ocupados.values())
        taxa = round(ocupados_total / capacidade_total * 100, 1) if capacidade_total else 0.0

        bagagens = self.bagagem_repo.contar_por_status()

        return ResumoDashboard(
            total_voos=self.voo_repo.total(),
            voos_por_status=self.voo_repo.contar_por_status(),
            total_aeronaves=len(self.aeronave_repo.listar()),
            total_passageiros=self.passageiro_repo.total(),
            vagas_livres=livres,
            vagas_ocupadas=ocupadas,
            total_vagas=len(vagas),
            taxa_ocupacao_media=taxa,
            check_ins_hoje=self.reserva_repo.contar_check_ins_do_dia(date.today()),
            bagagens_por_status=bagagens,
            bagagens_extraviadas=bagagens.get(StatusBagagem.EXTRAVIADA.value, 0),
            proximos_voos=self.voo_use_case.montar_lista(self.voo_repo.proximos()),
        )
