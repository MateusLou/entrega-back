from datetime import date, datetime, time

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from src.models.voo import Voo
from src.repositories.base_repository import BaseRepository
from src.utils.enums import SentidoVoo, StatusVoo, STATUS_VOO_ATIVO


class VooRepository(BaseRepository[Voo]):
    model = Voo

    #: Código IATA do aeroporto operado por esta plataforma.
    AEROPORTO_BASE = "CPT"

    def listar_filtrado(
        self,
        status: StatusVoo | None = None,
        terminal_id: int | None = None,
        aeronave_id: int | None = None,
        origem: str | None = None,
        destino: str | None = None,
        data: date | None = None,
        sentido: SentidoVoo | None = None,
        busca: str | None = None,
    ) -> list[Voo]:
        consulta = self.db.query(Voo).options(
            joinedload(Voo.aeronave), joinedload(Voo.terminal)
        )
        if status is not None:
            consulta = consulta.filter(Voo.status == status)
        if terminal_id is not None:
            consulta = consulta.filter(Voo.terminal_id == terminal_id)
        if aeronave_id is not None:
            consulta = consulta.filter(Voo.aeronave_id == aeronave_id)
        if origem:
            consulta = consulta.filter(Voo.origem == origem.upper())
        if destino:
            consulta = consulta.filter(Voo.destino == destino.upper())
        if busca:
            consulta = consulta.filter(Voo.codigo.like(f"%{busca.upper()}%"))
        if sentido is SentidoVoo.CHEGADA:
            consulta = consulta.filter(Voo.destino == self.AEROPORTO_BASE)
        elif sentido is SentidoVoo.PARTIDA:
            consulta = consulta.filter(Voo.origem == self.AEROPORTO_BASE)
        if data is not None:
            inicio = datetime.combine(data, time.min)
            fim = datetime.combine(data, time.max)
            consulta = consulta.filter(Voo.partida_prevista.between(inicio, fim))
        return list(consulta.order_by(Voo.partida_prevista).all())

    def buscar_por_codigo(self, codigo: str) -> Voo | None:
        return self.db.query(Voo).filter(Voo.codigo == codigo.upper()).first()

    def listar_por_aeronave(self, aeronave_id: int) -> list[Voo]:
        return list(
            self.db.query(Voo)
            .filter(Voo.aeronave_id == aeronave_id)
            .order_by(Voo.partida_prevista)
            .all()
        )

    def proximos(self, limite: int = 8) -> list[Voo]:
        return list(
            self.db.query(Voo)
            .options(joinedload(Voo.aeronave), joinedload(Voo.terminal))
            .filter(Voo.status.in_(STATUS_VOO_ATIVO))
            .order_by(Voo.partida_prevista)
            .limit(limite)
            .all()
        )

    def contar_por_status(self) -> dict[str, int]:
        linhas = self.db.query(Voo.status, func.count(Voo.id)).group_by(Voo.status).all()
        contagem = {s.value: 0 for s in StatusVoo}
        for status, total in linhas:
            contagem[status.value] = int(total)
        return contagem

    def total(self) -> int:
        return int(self.db.query(func.count(Voo.id)).scalar() or 0)
