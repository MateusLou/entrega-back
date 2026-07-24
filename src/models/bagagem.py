from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base
from src.utils.enums import StatusBagagem

if TYPE_CHECKING:
    from src.models.reserva import Reserva


class Bagagem(Base):
    """Mala despachada.

    Aponta para uma única reserva, o que garante que a mala tenha um só dono
    (o passageiro) e ao mesmo tempo saiba em qual voo está embarcada.
    """

    __tablename__ = "bagagens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    etiqueta: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    reserva_id: Mapped[int] = mapped_column(
        ForeignKey("reservas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    peso_kg: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    status: Mapped[StatusBagagem] = mapped_column(
        SAEnum(
            StatusBagagem, name="status_bagagem", values_callable=lambda e: [i.value for i in e]
        ),
        nullable=False,
        default=StatusBagagem.DESPACHADA,
        index=True,
    )
    local_atual: Mapped[str | None] = mapped_column(String(80))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    reserva: Mapped["Reserva"] = relationship(back_populates="bagagens", lazy="joined")
