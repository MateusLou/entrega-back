from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base
from src.utils.enums import StatusReserva

if TYPE_CHECKING:
    from src.models.bagagem import Bagagem
    from src.models.passageiro import Passageiro
    from src.models.voo import Voo


class Reserva(Base):
    """Tabela intermediária passageiro <-> voo (relação muitos-para-muitos ao longo do tempo).

    Carrega o estado operacional do passageiro naquele voo: confirmado, com check-in
    feito, embarcado, no-show, realocado ou cancelado.
    """

    __tablename__ = "reservas"
    __table_args__ = (
        UniqueConstraint("passageiro_id", "voo_id", name="uq_reserva_passageiro_voo"),
        UniqueConstraint("voo_id", "assento", name="uq_reserva_voo_assento"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    passageiro_id: Mapped[int] = mapped_column(
        ForeignKey("passageiros.id", ondelete="CASCADE"), nullable=False, index=True
    )
    voo_id: Mapped[int] = mapped_column(
        ForeignKey("voos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assento: Mapped[str | None] = mapped_column(String(5))
    status: Mapped[StatusReserva] = mapped_column(
        SAEnum(
            StatusReserva, name="status_reserva", values_callable=lambda e: [i.value for i in e]
        ),
        nullable=False,
        default=StatusReserva.CONFIRMADA,
        index=True,
    )
    check_in_em: Mapped[datetime | None] = mapped_column(DateTime)
    reserva_origem_id: Mapped[int | None] = mapped_column(
        ForeignKey("reservas.id", ondelete="SET NULL"), index=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    passageiro: Mapped["Passageiro"] = relationship(back_populates="reservas", lazy="joined")
    voo: Mapped["Voo"] = relationship(back_populates="reservas", lazy="joined")
    bagagens: Mapped[list["Bagagem"]] = relationship(
        back_populates="reserva", cascade="all, delete-orphan"
    )
    reserva_origem: Mapped["Reserva | None"] = relationship(remote_side=[id])
