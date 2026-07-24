"""Models SQLAlchemy. O `import *` daqui é usado por alembic/env.py."""

from src.models.aeronave import Aeronave
from src.models.alocacao_vaga import AlocacaoVaga
from src.models.bagagem import Bagagem
from src.models.passageiro import Passageiro
from src.models.reserva import Reserva
from src.models.terminal import Terminal
from src.models.vaga import Vaga
from src.models.voo import Voo

__all__ = [
    "Aeronave",
    "AlocacaoVaga",
    "Bagagem",
    "Passageiro",
    "Reserva",
    "Terminal",
    "Vaga",
    "Voo",
]
