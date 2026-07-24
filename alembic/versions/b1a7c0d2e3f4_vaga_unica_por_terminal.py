"""vaga_unica_por_terminal

O código da vaga era único no aeroporto inteiro, o que impedia o terminal nacional e o
internacional de terem cada um a sua posição "A1". A unicidade passa a ser por terminal.

Revision ID: b1a7c0d2e3f4
Revises: e3d675921fd2
Create Date: 2026-07-24 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b1a7c0d2e3f4'
down_revision: Union[str, Sequence[str], None] = 'e3d675921fd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Troca a unicidade global do código pela unicidade dentro do terminal."""
    # A UniqueConstraint sem nome da migration inicial vira, no MySQL, um índice
    # com o nome da própria coluna.
    op.drop_constraint('codigo', 'vagas', type_='unique')
    op.create_unique_constraint(
        'uq_vaga_terminal_codigo', 'vagas', ['terminal_id', 'codigo']
    )


def downgrade() -> None:
    """Volta para o código único no aeroporto inteiro."""
    op.drop_constraint('uq_vaga_terminal_codigo', 'vagas', type_='unique')
    op.create_unique_constraint('codigo', 'vagas', ['codigo'])
