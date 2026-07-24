from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base
from src.utils.enums import StatusVaga, TipoVaga

if TYPE_CHECKING:
    from src.models.alocacao_vaga import AlocacaoVaga
    from src.models.terminal import Terminal


class Vaga(Base):
    """Posição de estacionamento de aeronave: gate de embarque ou posição remota."""

    __tablename__ = "vagas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    terminal_id: Mapped[int] = mapped_column(
        ForeignKey("terminais.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[TipoVaga] = mapped_column(
        SAEnum(TipoVaga, name="tipo_vaga", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=TipoVaga.GATE,
    )
    status: Mapped[StatusVaga] = mapped_column(
        SAEnum(StatusVaga, name="status_vaga", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=StatusVaga.LIVRE,
        index=True,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    terminal: Mapped["Terminal"] = relationship(back_populates="vagas")
    alocacoes: Mapped[list["AlocacaoVaga"]] = relationship(
        back_populates="vaga", cascade="all, delete-orphan"
    )
