from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base

if TYPE_CHECKING:
    from src.models.voo import Voo


class Aeronave(Base):
    """Aeronave operada no aeroporto. A capacidade define os assentos do voo."""

    __tablename__ = "aeronaves"
    __table_args__ = (CheckConstraint("capacidade > 0", name="ck_aeronave_capacidade"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prefixo: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    modelo: Mapped[str] = mapped_column(String(60), nullable=False)
    companhia: Mapped[str] = mapped_column(String(60), nullable=False)
    capacidade: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    voos: Mapped[list["Voo"]] = relationship(back_populates="aeronave")
