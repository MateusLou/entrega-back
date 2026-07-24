from sqlalchemy.orm import Session

from src.entities.terminal import TerminalResumo
from src.entities.vaga import VagaAtualizar, VagaCriar, VagaResposta
from src.models.vaga import Vaga
from src.repositories.terminal_repository import TerminalRepository
from src.repositories.vaga_repository import VagaRepository
from src.utils.enums import StatusVaga, TipoVaga
from src.utils.exceptions import Conflito, NaoEncontrado, RegraDeNegocio


class VagaUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repo = VagaRepository(db)
        self.terminal_repo = TerminalRepository(db)

    def _montar(self, vaga: Vaga, ativas: dict[int, object]) -> VagaResposta:
        resposta = VagaResposta.model_validate(vaga)
        resposta.terminal = TerminalResumo.model_validate(vaga.terminal)
        alocacao = ativas.get(vaga.id)
        if alocacao is not None:
            resposta.voo_atual = alocacao.voo.codigo
        return resposta

    def listar(
        self,
        terminal_id: int | None = None,
        status: StatusVaga | None = None,
        tipo: TipoVaga | None = None,
    ) -> list[VagaResposta]:
        ativas = self.repo.alocacoes_ativas_por_vaga()
        return [self._montar(v, ativas) for v in self.repo.listar_filtrado(terminal_id, status, tipo)]

    def obter_model(self, id_: int) -> Vaga:
        vaga = self.repo.buscar(id_)
        if vaga is None:
            raise NaoEncontrado(f"Vaga {id_} não encontrada.")
        return vaga

    def obter(self, id_: int) -> VagaResposta:
        return self._montar(self.obter_model(id_), self.repo.alocacoes_ativas_por_vaga())

    def criar(self, dados: VagaCriar) -> VagaResposta:
        codigo = dados.codigo.upper()
        terminal = self.terminal_repo.buscar(dados.terminal_id)
        if terminal is None:
            raise NaoEncontrado(f"Terminal {dados.terminal_id} não encontrado.")
        if self.repo.buscar_por_codigo(dados.terminal_id, codigo):
            raise Conflito(f"O terminal '{terminal.nome}' já tem uma vaga '{codigo}'.")
        vaga = self.repo.criar(**{**dados.model_dump(), "codigo": codigo})
        return self._montar(vaga, self.repo.alocacoes_ativas_por_vaga())

    def atualizar(self, id_: int, dados: VagaAtualizar) -> VagaResposta:
        vaga = self.obter_model(id_)
        campos = dados.model_dump(exclude_unset=True)
        if campos.get("terminal_id") and self.terminal_repo.buscar(campos["terminal_id"]) is None:
            raise NaoEncontrado(f"Terminal {campos['terminal_id']} não encontrado.")

        # Mudar o código ou o terminal pode colidir com outra vaga do terminal de destino.
        if campos.get("codigo"):
            campos["codigo"] = campos["codigo"].upper()
        codigo = campos.get("codigo", vaga.codigo)
        terminal_id = campos.get("terminal_id", vaga.terminal_id)
        if codigo != vaga.codigo or terminal_id != vaga.terminal_id:
            existente = self.repo.buscar_por_codigo(terminal_id, codigo)
            if existente is not None and existente.id != vaga.id:
                raise Conflito(f"O terminal de destino já tem uma vaga '{codigo}'.")

        novo_status = campos.get("status")
        if novo_status and novo_status != StatusVaga.OCUPADA and vaga.status == StatusVaga.OCUPADA:
            ativas = self.repo.alocacoes_ativas_por_vaga()
            if vaga.id in ativas:
                raise Conflito(
                    "A vaga tem uma alocação ativa. Libere a alocação antes de mudar o status."
                )
        self.repo.atualizar(vaga, **campos)
        return self._montar(vaga, self.repo.alocacoes_ativas_por_vaga())

    def remover(self, id_: int) -> None:
        vaga = self.obter_model(id_)
        if vaga.id in self.repo.alocacoes_ativas_por_vaga():
            raise RegraDeNegocio("Não é possível remover uma vaga com alocação ativa.")
        self.repo.remover(vaga)
