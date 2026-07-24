from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base
from src.utils.enums import TipoTerminal

if TYPE_CHECKING:
    from src.models.vaga import Vaga
    from src.models.voo import Voo


class Terminal(Base):
    """Terminal do aeroporto (nacional ou internacional)."""

    __tablename__ = "terminais"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    tipo: Mapped[TipoTerminal] = mapped_column(
        SAEnum(TipoTerminal, name="tipo_terminal", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    vagas: Mapped[list["Vaga"]] = relationship(
        back_populates="terminal", cascade="all, delete-orphan"
    )
    voos: Mapped[list["Voo"]] = relationship(back_populates="terminal")
