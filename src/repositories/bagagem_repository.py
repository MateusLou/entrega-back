from sqlalchemy import func
from sqlalchemy.orm import joinedload

from src.models.bagagem import Bagagem
from src.models.reserva import Reserva
from src.repositories.base_repository import BaseRepository
from src.utils.enums import StatusBagagem


class BagagemRepository(BaseRepository[Bagagem]):
    model = Bagagem

    def _consulta_base(self):
        return self.db.query(Bagagem).options(
            joinedload(Bagagem.reserva).joinedload(Reserva.passageiro),
            joinedload(Bagagem.reserva).joinedload(Reserva.voo),
        )

    def listar_filtrado(
        self,
        status: StatusBagagem | None = None,
        reserva_id: int | None = None,
        voo_id: int | None = None,
        passageiro_id: int | None = None,
        etiqueta: str | None = None,
    ) -> list[Bagagem]:
        consulta = self._consulta_base()
        if status is not None:
            consulta = consulta.filter(Bagagem.status == status)
        if reserva_id is not None:
            consulta = consulta.filter(Bagagem.reserva_id == reserva_id)
        if etiqueta:
            consulta = consulta.filter(Bagagem.etiqueta.like(f"%{etiqueta.upper()}%"))
        if voo_id is not None or passageiro_id is not None:
            consulta = consulta.join(Reserva, Bagagem.reserva_id == Reserva.id)
            if voo_id is not None:
                consulta = consulta.filter(Reserva.voo_id == voo_id)
            if passageiro_id is not None:
                consulta = consulta.filter(Reserva.passageiro_id == passageiro_id)
        return list(consulta.order_by(Bagagem.id).all())

    def buscar_por_etiqueta(self, etiqueta: str) -> Bagagem | None:
        return self._consulta_base().filter(Bagagem.etiqueta == etiqueta.upper()).first()

    def buscar_com_relacoes(self, id_: int) -> Bagagem | None:
        return self._consulta_base().filter(Bagagem.id == id_).first()

    def contar_por_status(self) -> dict[str, int]:
        linhas = self.db.query(Bagagem.status, func.count(Bagagem.id)).group_by(Bagagem.status).all()
        contagem = {s.value: 0 for s in StatusBagagem}
        for status, total in linhas:
            contagem[status.value] = int(total)
        return contagem

    def proximo_numero_etiqueta(self) -> int:
        return int(self.db.query(func.count(Bagagem.id)).scalar() or 0) + 1
