from datetime import datetime

from sqlalchemy.orm import Session

from src.entities.passageiro import PassageiroResumo
from src.entities.reserva import RealocarReserva, ReservaCriar, ReservaResposta
from src.entities.voo import VooResumo
from src.models.reserva import Reserva
from src.repositories.passageiro_repository import PassageiroRepository
from src.repositories.reserva_repository import ReservaRepository
from src.repositories.voo_repository import VooRepository
from src.utils.assentos import assento_valido, proximo_assento_livre
from src.utils.enums import (
    STATUS_RESERVA_OCUPANDO_ASSENTO,
    STATUS_VOO_ACEITA_RESERVA,
    StatusReserva,
    StatusVoo,
)
from src.utils.exceptions import Conflito, NaoEncontrado, RegraDeNegocio


class ReservaUseCase:
    """Regras do vínculo passageiro <-> voo: reserva, check-in, no-show e realocação."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ReservaRepository(db)
        self.voo_repo = VooRepository(db)
        self.passageiro_repo = PassageiroRepository(db)

    # --- montagem de resposta -------------------------------------------------

    def _montar(self, reserva: Reserva, bagagens: dict[int, int]) -> ReservaResposta:
        resposta = ReservaResposta.model_validate(reserva)
        resposta.passageiro = PassageiroResumo.model_validate(reserva.passageiro)
        resposta.voo = VooResumo.model_validate(reserva.voo)
        resposta.total_bagagens = bagagens.get(reserva.id, 0)
        return resposta

    def montar_lista(self, reservas: list[Reserva]) -> list[ReservaResposta]:
        bagagens = self.repo.contar_bagagens_em_lote([r.id for r in reservas])
        return [self._montar(r, bagagens) for r in reservas]

    # --- consultas ------------------------------------------------------------

    def listar(
        self,
        voo_id: int | None = None,
        passageiro_id: int | None = None,
        status: StatusReserva | None = None,
    ) -> list[ReservaResposta]:
        return self.montar_lista(self.repo.listar_filtrado(voo_id, passageiro_id, status))

    def obter_model(self, id_: int) -> Reserva:
        reserva = self.repo.buscar(id_)
        if reserva is None:
            raise NaoEncontrado(f"Reserva {id_} não encontrada.")
        return reserva

    def obter(self, id_: int) -> ReservaResposta:
        return self.montar_lista([self.obter_model(id_)])[0]

    # --- criação --------------------------------------------------------------

    def _resolver_assento(self, voo_id: int, capacidade: int, assento: str | None) -> str | None:
        """Valida o assento pedido ou escolhe o próximo livre."""
        ocupados = self.repo.assentos_ocupados(voo_id)
        if assento:
            assento = assento.upper()
            if not assento_valido(capacidade, assento):
                raise RegraDeNegocio(
                    f"O assento '{assento}' não existe em uma aeronave de {capacidade} lugares."
                )
            if assento in ocupados:
                raise Conflito(f"O assento '{assento}' já está ocupado neste voo.")
            return assento
        return proximo_assento_livre(capacidade, ocupados)

    def criar(self, dados: ReservaCriar) -> ReservaResposta:
        passageiro = self.passageiro_repo.buscar(dados.passageiro_id)
        if passageiro is None:
            raise NaoEncontrado(f"Passageiro {dados.passageiro_id} não encontrado.")
        voo = self.voo_repo.buscar(dados.voo_id)
        if voo is None:
            raise NaoEncontrado(f"Voo {dados.voo_id} não encontrado.")

        if voo.status not in STATUS_VOO_ACEITA_RESERVA:
            raise Conflito(
                f"O voo {voo.codigo} está com status {voo.status.value} e não aceita novas reservas."
            )

        ocupados = self.repo.contar_ocupados(voo.id)
        if ocupados >= voo.aeronave.capacidade:
            raise Conflito(
                f"O voo {voo.codigo} está lotado "
                f"({ocupados}/{voo.aeronave.capacidade} assentos ocupados)."
            )

        assento = self._resolver_assento(voo.id, voo.aeronave.capacidade, dados.assento)

        # A unique (passageiro_id, voo_id) impede duas linhas para o mesmo par:
        # se já houve uma reserva encerrada nesse voo, ela é reaproveitada.
        existente = self.repo.buscar_por_passageiro_e_voo(passageiro.id, voo.id)
        if existente is not None:
            if existente.status in STATUS_RESERVA_OCUPANDO_ASSENTO:
                raise Conflito(
                    f"{passageiro.nome} já possui uma reserva ativa no voo {voo.codigo}."
                )
            existente.status = StatusReserva.CONFIRMADA
            existente.assento = assento
            existente.check_in_em = None
            self.db.commit()
            self.db.refresh(existente)
            return self.obter(existente.id)

        reserva = self.repo.criar(
            passageiro_id=passageiro.id,
            voo_id=voo.id,
            assento=assento,
            status=StatusReserva.CONFIRMADA,
        )
        return self.obter(reserva.id)

    # --- operações ------------------------------------------------------------

    def check_in(self, id_: int) -> ReservaResposta:
        reserva = self.obter_model(id_)
        if reserva.status is StatusReserva.CHECK_IN_FEITO:
            raise Conflito("O check-in desta reserva já foi realizado.")
        if reserva.status is not StatusReserva.CONFIRMADA:
            raise Conflito(
                f"Só é possível fazer check-in de uma reserva CONFIRMADA "
                f"(status atual: {reserva.status.value})."
            )
        voo = reserva.voo
        if voo.status not in (StatusVoo.NO_HORARIO, StatusVoo.ATRASADO, StatusVoo.EMBARQUE):
            raise Conflito(
                f"O voo {voo.codigo} está {voo.status.value} e não aceita check-in."
            )

        if not reserva.assento:
            ocupados = self.repo.assentos_ocupados(voo.id)
            assento = proximo_assento_livre(voo.aeronave.capacidade, ocupados)
            if assento is None:
                raise Conflito(f"Não há assentos livres no voo {voo.codigo}.")
            reserva.assento = assento

        reserva.status = StatusReserva.CHECK_IN_FEITO
        reserva.check_in_em = datetime.now()
        self.db.commit()
        return self.obter(reserva.id)

    def no_show(self, id_: int) -> ReservaResposta:
        reserva = self.obter_model(id_)
        if reserva.status not in (StatusReserva.CONFIRMADA, StatusReserva.CHECK_IN_FEITO):
            raise Conflito(
                f"Só uma reserva ativa pode ser marcada como no-show "
                f"(status atual: {reserva.status.value})."
            )
        if reserva.voo.status not in (StatusVoo.EMBARQUE, StatusVoo.FINALIZADO):
            raise Conflito(
                "O no-show só pode ser registrado depois que o voo entra em embarque."
            )
        reserva.status = StatusReserva.NO_SHOW
        reserva.assento = None  # devolve o assento para o inventário do voo
        self.db.commit()
        return self.obter(reserva.id)

    def cancelar(self, id_: int) -> ReservaResposta:
        reserva = self.obter_model(id_)
        if reserva.status in (StatusReserva.CANCELADA, StatusReserva.REALOCADA):
            raise Conflito(f"A reserva já está {reserva.status.value}.")
        if reserva.status is StatusReserva.EMBARCADA:
            raise Conflito("Não é possível cancelar a reserva de um passageiro já embarcado.")
        reserva.status = StatusReserva.CANCELADA
        reserva.assento = None
        self.db.commit()
        return self.obter(reserva.id)

    def realocar(self, id_: int, dados: RealocarReserva) -> ReservaResposta:
        """Move o passageiro (e as malas dele) para outro voo com o mesmo destino."""
        origem = self.obter_model(id_)
        voo_origem = origem.voo

        pode_realocar = (
            origem.status is StatusReserva.NO_SHOW
            or voo_origem.status is StatusVoo.CANCELADO
        )
        if not pode_realocar:
            raise Conflito(
                "Só é possível realocar um passageiro que perdeu o voo (NO_SHOW) "
                "ou cujo voo foi cancelado."
            )

        destino = self.voo_repo.buscar(dados.voo_destino_id)
        if destino is None:
            raise NaoEncontrado(f"Voo {dados.voo_destino_id} não encontrado.")
        if destino.id == voo_origem.id:
            raise RegraDeNegocio("O voo de destino precisa ser diferente do voo original.")
        if destino.destino != voo_origem.destino:
            raise RegraDeNegocio(
                f"O voo {destino.codigo} vai para {destino.destino}, "
                f"mas o passageiro precisa chegar em {voo_origem.destino}."
            )
        if destino.status not in STATUS_VOO_ACEITA_RESERVA:
            raise Conflito(
                f"O voo {destino.codigo} está {destino.status.value} e não aceita realocação."
            )
        if destino.partida_prevista <= datetime.now():
            raise RegraDeNegocio(
                f"O voo {destino.codigo} já partiu. Escolha um voo com partida futura."
            )

        ocupados = self.repo.contar_ocupados(destino.id)
        if ocupados >= destino.aeronave.capacidade:
            raise Conflito(
                f"O voo {destino.codigo} está lotado "
                f"({ocupados}/{destino.aeronave.capacidade} assentos ocupados)."
            )

        assento = self._resolver_assento(destino.id, destino.aeronave.capacidade, dados.assento)

        origem.status = StatusReserva.REALOCADA
        origem.assento = None

        nova = self.repo.buscar_por_passageiro_e_voo(origem.passageiro_id, destino.id)
        if nova is not None:
            if nova.status in STATUS_RESERVA_OCUPANDO_ASSENTO:
                raise Conflito(
                    f"{origem.passageiro.nome} já possui uma reserva ativa no voo {destino.codigo}."
                )
            nova.status = StatusReserva.CONFIRMADA
            nova.assento = assento
            nova.check_in_em = None
            nova.reserva_origem_id = origem.id
        else:
            nova = Reserva(
                passageiro_id=origem.passageiro_id,
                voo_id=destino.id,
                assento=assento,
                status=StatusReserva.CONFIRMADA,
                reserva_origem_id=origem.id,
            )
            self.db.add(nova)
        self.db.flush()

        # As malas seguem o passageiro para o novo voo.
        for bagagem in list(origem.bagagens):
            bagagem.reserva_id = nova.id

        self.db.commit()
        return self.obter(nova.id)
