from sqlalchemy.orm import Session

from src.entities.passageiro import (
    PassageiroAtualizar,
    PassageiroCriar,
    PassageiroResposta,
)
from src.models.passageiro import Passageiro
from src.repositories.passageiro_repository import PassageiroRepository
from src.repositories.reserva_repository import ReservaRepository
from src.utils.enums import STATUS_RESERVA_OCUPANDO_ASSENTO
from src.utils.exceptions import Conflito, NaoEncontrado, RegraDeNegocio


class PassageiroUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PassageiroRepository(db)
        self.reserva_repo = ReservaRepository(db)

    def _montar(self, passageiro: Passageiro, contagens: dict[int, int]) -> PassageiroResposta:
        resposta = PassageiroResposta.model_validate(passageiro)
        resposta.total_reservas = contagens.get(passageiro.id, 0)
        return resposta

    def listar(self, busca: str | None = None) -> list[PassageiroResposta]:
        contagens = self.reserva_repo.contar_por_passageiro()
        return [self._montar(p, contagens) for p in self.repo.listar_filtrado(busca)]

    def obter_model(self, id_: int) -> Passageiro:
        passageiro = self.repo.buscar(id_)
        if passageiro is None:
            raise NaoEncontrado(f"Passageiro {id_} não encontrado.")
        return passageiro

    def obter(self, id_: int) -> PassageiroResposta:
        return self._montar(self.obter_model(id_), self.reserva_repo.contar_por_passageiro())

    def criar(self, dados: PassageiroCriar) -> PassageiroResposta:
        if self.repo.buscar_por_documento(dados.documento):
            raise Conflito(f"Já existe um passageiro com o documento '{dados.documento}'.")
        passageiro = self.repo.criar(**dados.model_dump())
        return self._montar(passageiro, self.reserva_repo.contar_por_passageiro())

    def atualizar(self, id_: int, dados: PassageiroAtualizar) -> PassageiroResposta:
        passageiro = self.obter_model(id_)
        campos = dados.model_dump(exclude_unset=True)
        novo_doc = campos.get("documento")
        if (
            novo_doc
            and novo_doc != passageiro.documento
            and self.repo.buscar_por_documento(novo_doc)
        ):
            raise Conflito(f"Já existe um passageiro com o documento '{novo_doc}'.")
        self.repo.atualizar(passageiro, **campos)
        return self._montar(passageiro, self.reserva_repo.contar_por_passageiro())

    def remover(self, id_: int) -> None:
        passageiro = self.obter_model(id_)
        ativas = [r for r in passageiro.reservas if r.status in STATUS_RESERVA_OCUPANDO_ASSENTO]
        if ativas:
            raise RegraDeNegocio(
                "Não é possível remover um passageiro com reservas ativas. "
                "Cancele as reservas primeiro."
            )
        self.repo.remover(passageiro)
