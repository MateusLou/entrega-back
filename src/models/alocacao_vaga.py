from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base
from src.utils.enums import FinalidadeAlocacao

if TYPE_CHECKING:
    from src.models.vaga import Vaga
    from src.models.voo import Voo


class AlocacaoVaga(Base):
    """Tabela intermediária voo <-> vaga: um voo ocupa uma posição por um período."""

    __tablename__ = "alocacoes_vaga"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    voo_id: Mapped[int] = mapped_column(
        ForeignKey("voos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vaga_id: Mapped[int] = mapped_column(
        ForeignKey("vagas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fim: Mapped[datetime | None] = mapped_column(DateTime)
    finalidade: Mapped[FinalidadeAlocacao] = mapped_column(
        SAEnum(
            FinalidadeAlocacao,
            name="finalidade_alocacao",
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
        default=FinalidadeAlocacao.DESEMBARQUE,
    )
    ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    voo: Mapped["Voo"] = relationship(back_populates="alocacoes", lazy="joined")
    vaga: Mapped["Vaga"] = relationship(back_populates="alocacoes", lazy="joined")
