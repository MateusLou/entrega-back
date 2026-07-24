from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base
from src.utils.enums import StatusVoo

if TYPE_CHECKING:
    from src.models.aeronave import Aeronave
    from src.models.alocacao_vaga import AlocacaoVaga
    from src.models.reserva import Reserva
    from src.models.terminal import Terminal


class Voo(Base):
    """Voo que chega ou parte do aeroporto, sempre operado por uma aeronave."""

    __tablename__ = "voos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    origem: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    destino: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    partida_prevista: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    chegada_prevista: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    partida_real: Mapped[datetime | None] = mapped_column(DateTime)
    chegada_real: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[StatusVoo] = mapped_column(
        SAEnum(StatusVoo, name="status_voo", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=StatusVoo.NO_HORARIO,
        index=True,
    )
    aeronave_id: Mapped[int] = mapped_column(
        ForeignKey("aeronaves.id"), nullable=False, index=True
    )
    terminal_id: Mapped[int] = mapped_column(
        ForeignKey("terminais.id"), nullable=False, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    aeronave: Mapped["Aeronave"] = relationship(back_populates="voos", lazy="joined")
    terminal: Mapped["Terminal"] = relationship(back_populates="voos", lazy="joined")
    reservas: Mapped[list["Reserva"]] = relationship(
        back_populates="voo", cascade="all, delete-orphan"
    )
    alocacoes: Mapped[list["AlocacaoVaga"]] = relationship(
        back_populates="voo", cascade="all, delete-orphan"
    )
