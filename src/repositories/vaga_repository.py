from sqlalchemy.orm import joinedload

from src.models.alocacao_vaga import AlocacaoVaga
from src.models.vaga import Vaga
from src.repositories.base_repository import BaseRepository
from src.utils.enums import StatusVaga, TipoVaga


class VagaRepository(BaseRepository[Vaga]):
    model = Vaga

    def listar_filtrado(
        self,
        terminal_id: int | None = None,
        status: StatusVaga | None = None,
        tipo: TipoVaga | None = None,
    ) -> list[Vaga]:
        consulta = self.db.query(Vaga).options(joinedload(Vaga.terminal))
        if terminal_id is not None:
            consulta = consulta.filter(Vaga.terminal_id == terminal_id)
        if status is not None:
            consulta = consulta.filter(Vaga.status == status)
        if tipo is not None:
            consulta = consulta.filter(Vaga.tipo == tipo)
        return list(consulta.order_by(Vaga.codigo).all())

    def buscar_por_codigo(self, terminal_id: int, codigo: str) -> Vaga | None:
        """O código é único apenas dentro do terminal (uq_vaga_terminal_codigo)."""
        return (
            self.db.query(Vaga)
            .filter(Vaga.terminal_id == terminal_id, Vaga.codigo == codigo)
            .first()
        )

    def alocacoes_ativas_por_vaga(self) -> dict[int, AlocacaoVaga]:
        """Retorna {vaga_id: alocacao_ativa} para exibir qual voo está em cada vaga."""
        alocacoes = (
            self.db.query(AlocacaoVaga)
            .options(joinedload(AlocacaoVaga.voo))
            .filter(AlocacaoVaga.ativa.is_(True))
            .all()
        )
        return {a.vaga_id: a for a in alocacoes}
