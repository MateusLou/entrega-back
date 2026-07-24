from sqlalchemy import func

from src.models.terminal import Terminal
from src.models.vaga import Vaga
from src.repositories.base_repository import BaseRepository
from src.utils.enums import StatusVaga


class TerminalRepository(BaseRepository[Terminal]):
    model = Terminal

    def buscar_por_nome(self, nome: str) -> Terminal | None:
        return self.db.query(Terminal).filter(Terminal.nome == nome).first()

    def contar_vagas(self) -> dict[int, tuple[int, int]]:
        """Retorna {terminal_id: (total_vagas, vagas_livres)}."""
        linhas = (
            self.db.query(
                Vaga.terminal_id,
                func.count(Vaga.id),
                func.sum(func.if_(Vaga.status == StatusVaga.LIVRE, 1, 0)),
            )
            .group_by(Vaga.terminal_id)
            .all()
        )
        return {tid: (int(total), int(livres or 0)) for tid, total, livres in linhas}
