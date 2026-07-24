from sqlalchemy.orm import Session

from src.entities.bagagem import BagagemAtualizarStatus, BagagemCriar, BagagemResposta
from src.entities.passageiro import PassageiroResumo
from src.entities.voo import VooResumo
from src.models.bagagem import Bagagem
from src.repositories.bagagem_repository import BagagemRepository
from src.repositories.reserva_repository import ReservaRepository
from src.utils.enums import (
    STATUS_RESERVA_OCUPANDO_ASSENTO,
    StatusBagagem,
    TRANSICOES_BAGAGEM,
)
from src.utils.exceptions import Conflito, NaoEncontrado, RegraDeNegocio


class BagagemUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BagagemRepository(db)
        self.reserva_repo = ReservaRepository(db)

    def _montar(self, bagagem: Bagagem) -> BagagemResposta:
        resposta = BagagemResposta.model_validate(bagagem)
        resposta.passageiro = PassageiroResumo.model_validate(bagagem.reserva.passageiro)
        resposta.voo = VooResumo.model_validate(bagagem.reserva.voo)
        resposta.transicoes_permitidas = sorted(
            TRANSICOES_BAGAGEM[bagagem.status], key=lambda s: s.value
        )
        return resposta

    def listar(
        self,
        status: StatusBagagem | None = None,
        reserva_id: int | None = None,
        voo_id: int | None = None,
        passageiro_id: int | None = None,
        etiqueta: str | None = None,
    ) -> list[BagagemResposta]:
        bagagens = self.repo.listar_filtrado(status, reserva_id, voo_id, passageiro_id, etiqueta)
        return [self._montar(b) for b in bagagens]

    def obter_model(self, id_: int) -> Bagagem:
        bagagem = self.repo.buscar_com_relacoes(id_)
        if bagagem is None:
            raise NaoEncontrado(f"Bagagem {id_} não encontrada.")
        return bagagem

    def obter(self, id_: int) -> BagagemResposta:
        return self._montar(self.obter_model(id_))

    def rastrear(self, etiqueta: str) -> BagagemResposta:
        bagagem = self.repo.buscar_por_etiqueta(etiqueta)
        if bagagem is None:
            raise NaoEncontrado(f"Nenhuma bagagem encontrada com a etiqueta '{etiqueta}'.")
        return self._montar(bagagem)

    def _gerar_etiqueta(self) -> str:
        numero = self.repo.proximo_numero_etiqueta()
        while self.repo.buscar_por_etiqueta(f"CPT{numero:06d}") is not None:
            numero += 1
        return f"CPT{numero:06d}"

    def despachar(self, dados: BagagemCriar) -> BagagemResposta:
        reserva = self.reserva_repo.buscar(dados.reserva_id)
        if reserva is None:
            raise NaoEncontrado(f"Reserva {dados.reserva_id} não encontrada.")
        if reserva.status not in STATUS_RESERVA_OCUPANDO_ASSENTO:
            raise Conflito(
                f"A reserva está {reserva.status.value}; só é possível despachar malas "
                "em uma reserva ativa."
            )

        etiqueta = (dados.etiqueta or "").upper() or self._gerar_etiqueta()
        if self.repo.buscar_por_etiqueta(etiqueta) is not None:
            raise Conflito(f"Já existe uma bagagem com a etiqueta '{etiqueta}'.")

        bagagem = self.repo.criar(
            etiqueta=etiqueta,
            reserva_id=reserva.id,
            peso_kg=dados.peso_kg,
            status=StatusBagagem.DESPACHADA,
            local_atual=dados.local_atual or "Balcão de check-in",
        )
        return self.obter(bagagem.id)

    def alterar_status(self, id_: int, dados: BagagemAtualizarStatus) -> BagagemResposta:
        bagagem = self.obter_model(id_)
        if dados.status != bagagem.status:
            permitidas = TRANSICOES_BAGAGEM[bagagem.status]
            if dados.status not in permitidas:
                rotulos = ", ".join(sorted(s.value for s in permitidas)) or "nenhuma"
                raise Conflito(
                    f"Transição inválida: {bagagem.status.value} -> {dados.status.value}. "
                    f"Transições permitidas: {rotulos}."
                )
            bagagem.status = dados.status
        if dados.local_atual is not None:
            bagagem.local_atual = dados.local_atual
        self.db.commit()
        return self.obter(bagagem.id)

    def remover(self, id_: int) -> None:
        bagagem = self.obter_model(id_)
        if bagagem.status is StatusBagagem.CARREGADA:
            raise RegraDeNegocio(
                "Não é possível remover uma bagagem já carregada na aeronave."
            )
        self.repo.remover(bagagem)
