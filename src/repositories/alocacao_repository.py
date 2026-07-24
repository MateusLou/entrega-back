from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload

from src.models.alocacao_vaga import AlocacaoVaga
from src.repositories.base_repository import BaseRepository


class AlocacaoRepository(BaseRepository[AlocacaoVaga]):
    model = AlocacaoVaga

    def listar_por_voo(self, voo_id: int) -> list[AlocacaoVaga]:
        return list(
            self.db.query(AlocacaoVaga)
            .options(joinedload(AlocacaoVaga.vaga))
            .filter(AlocacaoVaga.voo_id == voo_id)
            .order_by(AlocacaoVaga.inicio.desc())
            .all()
        )

    def alocacao_ativa_do_voo(self, voo_id: int) -> AlocacaoVaga | None:
        return (
            self.db.query(AlocacaoVaga)
            .options(joinedload(AlocacaoVaga.vaga))
            .filter(AlocacaoVaga.voo_id == voo_id, AlocacaoVaga.ativa.is_(True))
            .first()
        )

    def alocacoes_ativas_em_lote(self, voo_ids: list[int]) -> dict[int, AlocacaoVaga]:
        if not voo_ids:
            return {}
        alocacoes = (
            self.db.query(AlocacaoVaga)
            .options(joinedload(AlocacaoVaga.vaga))
            .filter(AlocacaoVaga.voo_id.in_(voo_ids), AlocacaoVaga.ativa.is_(True))
            .all()
        )
        return {a.voo_id: a for a in alocacoes}

    def existe_conflito(self, vaga_id: int, inicio: datetime, fim: datetime | None) -> bool:
        """Verifica sobreposição de período com outra alocação da mesma vaga.

        Alocação sem `fim` é tratada como aberta (ocupa a vaga por tempo indeterminado).
        """
        consulta = self.db.query(AlocacaoVaga).filter(
            AlocacaoVaga.vaga_id == vaga_id, AlocacaoVaga.ativa.is_(True)
        )
        if fim is None:
            consulta = consulta.filter(
                or_(AlocacaoVaga.fim.is_(None), AlocacaoVaga.fim > inicio)
            )
        else:
            consulta = consulta.filter(
                and_(
                    AlocacaoVaga.inicio < fim,
                    or_(AlocacaoVaga.fim.is_(None), AlocacaoVaga.fim > inicio),
                )
            )
        return self.db.query(consulta.exists()).scalar() is True
