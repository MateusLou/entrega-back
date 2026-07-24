from sqlalchemy.orm import Session

from src.entities.aeronave import AeronaveAtualizar, AeronaveCriar, AeronaveResposta
from src.models.aeronave import Aeronave
from src.repositories.aeronave_repository import AeronaveRepository
from src.repositories.voo_repository import VooRepository
from src.utils.exceptions import Conflito, NaoEncontrado, RegraDeNegocio


class AeronaveUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AeronaveRepository(db)
        self.voo_repo = VooRepository(db)

    def _montar(self, aeronave: Aeronave, contagens: dict[int, int]) -> AeronaveResposta:
        resposta = AeronaveResposta.model_validate(aeronave)
        resposta.total_voos = contagens.get(aeronave.id, 0)
        return resposta

    def listar(self) -> list[AeronaveResposta]:
        contagens = self.repo.contar_voos()
        return [self._montar(a, contagens) for a in self.repo.listar()]

    def obter_model(self, id_: int) -> Aeronave:
        aeronave = self.repo.buscar(id_)
        if aeronave is None:
            raise NaoEncontrado(f"Aeronave {id_} não encontrada.")
        return aeronave

    def obter(self, id_: int) -> AeronaveResposta:
        return self._montar(self.obter_model(id_), self.repo.contar_voos())

    def criar(self, dados: AeronaveCriar) -> AeronaveResposta:
        prefixo = dados.prefixo.upper()
        if self.repo.buscar_por_prefixo(prefixo):
            raise Conflito(f"Já existe uma aeronave com o prefixo '{prefixo}'.")
        aeronave = self.repo.criar(**{**dados.model_dump(), "prefixo": prefixo})
        return self._montar(aeronave, self.repo.contar_voos())

    def atualizar(self, id_: int, dados: AeronaveAtualizar) -> AeronaveResposta:
        aeronave = self.obter_model(id_)
        campos = dados.model_dump(exclude_unset=True)
        if "prefixo" in campos and campos["prefixo"]:
            campos["prefixo"] = campos["prefixo"].upper()
            if campos["prefixo"] != aeronave.prefixo and self.repo.buscar_por_prefixo(
                campos["prefixo"]
            ):
                raise Conflito(f"Já existe uma aeronave com o prefixo '{campos['prefixo']}'.")
        self.repo.atualizar(aeronave, **campos)
        return self._montar(aeronave, self.repo.contar_voos())

    def remover(self, id_: int) -> None:
        aeronave = self.obter_model(id_)
        if aeronave.voos:
            raise RegraDeNegocio(
                "Não é possível remover uma aeronave com voos associados."
            )
        self.repo.remover(aeronave)
