from datetime import date, datetime, time

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from src.models.bagagem import Bagagem
from src.models.reserva import Reserva
from src.repositories.base_repository import BaseRepository
from src.utils.enums import StatusReserva, STATUS_RESERVA_OCUPANDO_ASSENTO


class ReservaRepository(BaseRepository[Reserva]):
    model = Reserva

    def listar_filtrado(
        self,
        voo_id: int | None = None,
        passageiro_id: int | None = None,
        status: StatusReserva | None = None,
    ) -> list[Reserva]:
        consulta = self.db.query(Reserva).options(
            joinedload(Reserva.passageiro), joinedload(Reserva.voo)
        )
        if voo_id is not None:
            consulta = consulta.filter(Reserva.voo_id == voo_id)
        if passageiro_id is not None:
            consulta = consulta.filter(Reserva.passageiro_id == passageiro_id)
        if status is not None:
            consulta = consulta.filter(Reserva.status == status)
        return list(consulta.order_by(Reserva.id).all())

    def buscar_por_passageiro_e_voo(self, passageiro_id: int, voo_id: int) -> Reserva | None:
        return (
            self.db.query(Reserva)
            .filter(Reserva.passageiro_id == passageiro_id, Reserva.voo_id == voo_id)
            .first()
        )

    def contar_ocupados(self, voo_id: int) -> int:
        return int(
            self.db.query(func.count(Reserva.id))
            .filter(
                Reserva.voo_id == voo_id,
                Reserva.status.in_(STATUS_RESERVA_OCUPANDO_ASSENTO),
            )
            .scalar()
            or 0
        )

    def contar_ocupados_em_lote(self, voo_ids: list[int]) -> dict[int, int]:
        """Uma única consulta para a ocupação de vários voos (evita N+1 nas listagens)."""
        if not voo_ids:
            return {}
        linhas = (
            self.db.query(Reserva.voo_id, func.count(Reserva.id))
            .filter(
                Reserva.voo_id.in_(voo_ids),
                Reserva.status.in_(STATUS_RESERVA_OCUPANDO_ASSENTO),
            )
            .group_by(Reserva.voo_id)
            .all()
        )
        return {vid: int(total) for vid, total in linhas}

    def assentos_ocupados(self, voo_id: int) -> set[str]:
        linhas = (
            self.db.query(Reserva.assento)
            .filter(Reserva.voo_id == voo_id, Reserva.assento.isnot(None))
            .all()
        )
        return {assento for (assento,) in linhas}

    def contar_bagagens_em_lote(self, reserva_ids: list[int]) -> dict[int, int]:
        if not reserva_ids:
            return {}
        linhas = (
            self.db.query(Bagagem.reserva_id, func.count(Bagagem.id))
            .filter(Bagagem.reserva_id.in_(reserva_ids))
            .group_by(Bagagem.reserva_id)
            .all()
        )
        return {rid: int(total) for rid, total in linhas}

    def contar_check_ins_do_dia(self, dia: date) -> int:
        inicio = datetime.combine(dia, time.min)
        fim = datetime.combine(dia, time.max)
        return int(
            self.db.query(func.count(Reserva.id))
            .filter(Reserva.check_in_em.between(inicio, fim))
            .scalar()
            or 0
        )

    def listar_ativas_do_voo(self, voo_id: int) -> list[Reserva]:
        return list(
            self.db.query(Reserva)
            .filter(
                Reserva.voo_id == voo_id,
                Reserva.status.in_(STATUS_RESERVA_OCUPANDO_ASSENTO),
            )
            .all()
        )

    def contar_por_passageiro(self) -> dict[int, int]:
        linhas = (
            self.db.query(Reserva.passageiro_id, func.count(Reserva.id))
            .group_by(Reserva.passageiro_id)
            .all()
        )
        return {pid: int(total) for pid, total in linhas}
