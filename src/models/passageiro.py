from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base

if TYPE_CHECKING:
    from src.models.reserva import Reserva


class Passageiro(Base):
    """Passageiro do aeroporto. Liga-se aos voos pela tabela intermediária `reservas`."""

    __tablename__ = "passageiros"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    documento: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    email: Mapped[str | None] = mapped_column(String(120))
    telefone: Mapped[str | None] = mapped_column(String(30))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    reservas: Mapped[list["Reserva"]] = relationship(
        back_populates="passageiro", cascade="all, delete-orphan"
    )
