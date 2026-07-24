from sqlalchemy.orm import Session

from src.entities.terminal import TerminalAtualizar, TerminalCriar, TerminalResposta
from src.models.terminal import Terminal
from src.repositories.terminal_repository import TerminalRepository
from src.utils.exceptions import Conflito, NaoEncontrado, RegraDeNegocio


class TerminalUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TerminalRepository(db)

    def _montar(self, terminal: Terminal, contagens: dict[int, tuple[int, int]]) -> TerminalResposta:
        total, livres = contagens.get(terminal.id, (0, 0))
        resposta = TerminalResposta.model_validate(terminal)
        resposta.total_vagas = total
        resposta.vagas_livres = livres
        return resposta

    def listar(self) -> list[TerminalResposta]:
        contagens = self.repo.contar_vagas()
        return [self._montar(t, contagens) for t in self.repo.listar()]

    def obter_model(self, id_: int) -> Terminal:
        terminal = self.repo.buscar(id_)
        if terminal is None:
            raise NaoEncontrado(f"Terminal {id_} não encontrado.")
        return terminal

    def obter(self, id_: int) -> TerminalResposta:
        return self._montar(self.obter_model(id_), self.repo.contar_vagas())

    def criar(self, dados: TerminalCriar) -> TerminalResposta:
        if self.repo.buscar_por_nome(dados.nome):
            raise Conflito(f"Já existe um terminal chamado '{dados.nome}'.")
        terminal = self.repo.criar(**dados.model_dump())
        return self._montar(terminal, self.repo.contar_vagas())

    def atualizar(self, id_: int, dados: TerminalAtualizar) -> TerminalResposta:
        terminal = self.obter_model(id_)
        campos = dados.model_dump(exclude_unset=True)
        novo_nome = campos.get("nome")
        if novo_nome and novo_nome != terminal.nome and self.repo.buscar_por_nome(novo_nome):
            raise Conflito(f"Já existe um terminal chamado '{novo_nome}'.")
        self.repo.atualizar(terminal, **campos)
        return self._montar(terminal, self.repo.contar_vagas())

    def remover(self, id_: int) -> None:
        terminal = self.obter_model(id_)
        if terminal.voos:
            raise RegraDeNegocio(
                "Não é possível remover um terminal com voos associados. "
                "Remova ou realoque os voos primeiro."
            )
        self.repo.remover(terminal)
