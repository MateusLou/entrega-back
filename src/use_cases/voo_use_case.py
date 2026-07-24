from datetime import date, datetime

from sqlalchemy.orm import Session

from src.entities.aeronave import AeronaveResumo
from src.entities.alocacao import AlocacaoCriar, AlocacaoResposta
from src.entities.terminal import TerminalResumo
from src.entities.vaga import VagaResumo
from src.entities.voo import OcupacaoVoo, VooAtualizar, VooCriar, VooResposta
from src.models.alocacao_vaga import AlocacaoVaga
from src.models.voo import Voo
from src.repositories.aeronave_repository import AeronaveRepository
from src.repositories.alocacao_repository import AlocacaoRepository
from src.repositories.reserva_repository import ReservaRepository
from src.repositories.terminal_repository import TerminalRepository
from src.repositories.vaga_repository import VagaRepository
from src.repositories.voo_repository import VooRepository
from src.utils.enums import (
    SentidoVoo,
    StatusReserva,
    StatusVaga,
    StatusVoo,
    TRANSICOES_VOO,
)
from src.utils.exceptions import Conflito, NaoEncontrado, RegraDeNegocio


class VooUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repo = VooRepository(db)
        self.aeronave_repo = AeronaveRepository(db)
        self.terminal_repo = TerminalRepository(db)
        self.vaga_repo = VagaRepository(db)
        self.alocacao_repo = AlocacaoRepository(db)
        self.reserva_repo = ReservaRepository(db)

    # --- montagem de resposta -------------------------------------------------

    @staticmethod
    def _ocupacao(capacidade: int, ocupados: int) -> OcupacaoVoo:
        disponiveis = max(capacidade - ocupados, 0)
        taxa = round(ocupados / capacidade * 100, 1) if capacidade else 0.0
        return OcupacaoVoo(
            capacidade=capacidade,
            ocupados=ocupados,
            disponiveis=disponiveis,
            taxa_ocupacao=taxa,
        )

    def _montar(
        self,
        voo: Voo,
        ocupados_por_voo: dict[int, int],
        alocacoes: dict[int, AlocacaoVaga],
    ) -> VooResposta:
        resposta = VooResposta.model_validate(voo)
        resposta.aeronave = AeronaveResumo.model_validate(voo.aeronave)
        resposta.terminal = TerminalResumo.model_validate(voo.terminal)
        resposta.ocupacao = self._ocupacao(
            voo.aeronave.capacidade, ocupados_por_voo.get(voo.id, 0)
        )
        alocacao = alocacoes.get(voo.id)
        if alocacao is not None:
            resposta.vaga_atual = VagaResumo.model_validate(alocacao.vaga)
        resposta.transicoes_permitidas = sorted(TRANSICOES_VOO[voo.status], key=lambda s: s.value)
        return resposta

    def montar_lista(self, voos: list[Voo]) -> list[VooResposta]:
        ids = [v.id for v in voos]
        ocupados = self.reserva_repo.contar_ocupados_em_lote(ids)
        alocacoes = self.alocacao_repo.alocacoes_ativas_em_lote(ids)
        return [self._montar(v, ocupados, alocacoes) for v in voos]

    # --- consultas ------------------------------------------------------------

    def listar(
        self,
        status: StatusVoo | None = None,
        terminal_id: int | None = None,
        aeronave_id: int | None = None,
        origem: str | None = None,
        destino: str | None = None,
        data: date | None = None,
        sentido: SentidoVoo | None = None,
        busca: str | None = None,
    ) -> list[VooResposta]:
        voos = self.repo.listar_filtrado(
            status=status,
            terminal_id=terminal_id,
            aeronave_id=aeronave_id,
            origem=origem,
            destino=destino,
            data=data,
            sentido=sentido,
            busca=busca,
        )
        return self.montar_lista(voos)

    def obter_model(self, id_: int) -> Voo:
        voo = self.repo.buscar(id_)
        if voo is None:
            raise NaoEncontrado(f"Voo {id_} não encontrado.")
        return voo

    def obter(self, id_: int) -> VooResposta:
        return self.montar_lista([self.obter_model(id_)])[0]

    def ocupacao(self, id_: int) -> OcupacaoVoo:
        voo = self.obter_model(id_)
        return self._ocupacao(voo.aeronave.capacidade, self.reserva_repo.contar_ocupados(id_))

    # --- escrita --------------------------------------------------------------

    def _validar_vinculos(self, aeronave_id: int | None, terminal_id: int | None) -> None:
        if aeronave_id is not None and self.aeronave_repo.buscar(aeronave_id) is None:
            raise NaoEncontrado(f"Aeronave {aeronave_id} não encontrada.")
        if terminal_id is not None and self.terminal_repo.buscar(terminal_id) is None:
            raise NaoEncontrado(f"Terminal {terminal_id} não encontrado.")

    def criar(self, dados: VooCriar) -> VooResposta:
        if self.repo.buscar_por_codigo(dados.codigo):
            raise Conflito(f"Já existe um voo com o código '{dados.codigo}'.")
        if dados.chegada_prevista <= dados.partida_prevista:
            raise RegraDeNegocio("A chegada prevista deve ser posterior à partida prevista.")
        if dados.origem == dados.destino:
            raise RegraDeNegocio("Origem e destino não podem ser iguais.")
        self._validar_vinculos(dados.aeronave_id, dados.terminal_id)
        voo = self.repo.criar(**dados.model_dump())
        return self.obter(voo.id)

    def atualizar(self, id_: int, dados: VooAtualizar) -> VooResposta:
        voo = self.obter_model(id_)
        campos = dados.model_dump(exclude_unset=True)
        if campos.get("codigo"):
            campos["codigo"] = campos["codigo"].upper()
            if campos["codigo"] != voo.codigo and self.repo.buscar_por_codigo(campos["codigo"]):
                raise Conflito(f"Já existe um voo com o código '{campos['codigo']}'.")
        for campo in ("origem", "destino"):
            if campos.get(campo):
                campos[campo] = campos[campo].upper()
        self._validar_vinculos(campos.get("aeronave_id"), campos.get("terminal_id"))

        partida = campos.get("partida_prevista", voo.partida_prevista)
        chegada = campos.get("chegada_prevista", voo.chegada_prevista)
        if chegada <= partida:
            raise RegraDeNegocio("A chegada prevista deve ser posterior à partida prevista.")
        if campos.get("origem", voo.origem) == campos.get("destino", voo.destino):
            raise RegraDeNegocio("Origem e destino não podem ser iguais.")

        nova_aeronave_id = campos.get("aeronave_id")
        if nova_aeronave_id and nova_aeronave_id != voo.aeronave_id:
            nova = self.aeronave_repo.buscar(nova_aeronave_id)
            ocupados = self.reserva_repo.contar_ocupados(voo.id)
            if nova.capacidade < ocupados:
                raise Conflito(
                    f"A aeronave '{nova.prefixo}' tem {nova.capacidade} assentos, "
                    f"menos que os {ocupados} passageiros já confirmados neste voo."
                )
        self.repo.atualizar(voo, **campos)
        return self.obter(voo.id)

    def remover(self, id_: int) -> None:
        voo = self.obter_model(id_)
        if self.reserva_repo.contar_ocupados(id_) > 0:
            raise RegraDeNegocio(
                "Não é possível remover um voo com passageiros confirmados. "
                "Cancele o voo em vez de removê-lo."
            )
        self.repo.remover(voo)

    # --- máquina de estados ---------------------------------------------------

    def alterar_status(self, id_: int, novo_status: StatusVoo) -> VooResposta:
        voo = self.obter_model(id_)
        if novo_status == voo.status:
            return self.obter(voo.id)

        permitidas = TRANSICOES_VOO[voo.status]
        if novo_status not in permitidas:
            rotulos = ", ".join(sorted(s.value for s in permitidas)) or "nenhuma"
            raise Conflito(
                f"Transição inválida: {voo.status.value} -> {novo_status.value}. "
                f"Transições permitidas: {rotulos}."
            )

        voo.status = novo_status
        agora = datetime.now()

        if novo_status is StatusVoo.FINALIZADO:
            # Quem estava com check-in feito é considerado embarcado.
            for reserva in self.reserva_repo.listar_ativas_do_voo(voo.id):
                if reserva.status is StatusReserva.CHECK_IN_FEITO:
                    reserva.status = StatusReserva.EMBARCADA
            voo.chegada_real = voo.chegada_real or agora
            self._liberar_alocacao_ativa(voo.id, agora)

        elif novo_status is StatusVoo.EMBARQUE:
            voo.partida_real = voo.partida_real or agora

        elif novo_status is StatusVoo.CANCELADO:
            # Cancelamento em cascata: reservas ativas caem e a vaga é devolvida.
            for reserva in self.reserva_repo.listar_ativas_do_voo(voo.id):
                reserva.status = StatusReserva.CANCELADA
            self._liberar_alocacao_ativa(voo.id, agora)

        self.db.commit()
        return self.obter(voo.id)

    # --- alocação de vagas ----------------------------------------------------

    def _liberar_alocacao_ativa(self, voo_id: int, quando: datetime) -> None:
        alocacao = self.alocacao_repo.alocacao_ativa_do_voo(voo_id)
        if alocacao is None:
            return
        alocacao.ativa = False
        alocacao.fim = alocacao.fim or quando
        alocacao.vaga.status = StatusVaga.LIVRE

    def listar_alocacoes(self, voo_id: int) -> list[AlocacaoResposta]:
        self.obter_model(voo_id)
        return [
            AlocacaoResposta.model_validate(a) for a in self.alocacao_repo.listar_por_voo(voo_id)
        ]

    def alocar_vaga(self, voo_id: int, dados: AlocacaoCriar) -> AlocacaoResposta:
        voo = self.obter_model(voo_id)
        if voo.status in (StatusVoo.FINALIZADO, StatusVoo.CANCELADO):
            raise Conflito(
                f"Não é possível alocar vaga para um voo {voo.status.value.lower()}."
            )

        vaga = self.vaga_repo.buscar(dados.vaga_id)
        if vaga is None:
            raise NaoEncontrado(f"Vaga {dados.vaga_id} não encontrada.")
        if vaga.terminal_id != voo.terminal_id:
            raise RegraDeNegocio(
                f"A vaga '{vaga.codigo}' pertence a outro terminal. "
                "A vaga precisa estar no mesmo terminal do voo."
            )
        if vaga.status is StatusVaga.MANUTENCAO:
            raise Conflito(f"A vaga '{vaga.codigo}' está em manutenção.")

        if self.alocacao_repo.alocacao_ativa_do_voo(voo_id) is not None:
            raise Conflito(
                "Este voo já ocupa uma vaga. Libere a alocação atual antes de alocar outra."
            )

        inicio = dados.inicio or datetime.now()
        if dados.fim is not None and dados.fim <= inicio:
            raise RegraDeNegocio("O fim da alocação deve ser posterior ao início.")
        if self.alocacao_repo.existe_conflito(vaga.id, inicio, dados.fim):
            raise Conflito(
                f"A vaga '{vaga.codigo}' já está ocupada nesse período."
            )

        alocacao = self.alocacao_repo.criar(
            voo_id=voo_id,
            vaga_id=vaga.id,
            inicio=inicio,
            fim=dados.fim,
            finalidade=dados.finalidade,
            ativa=True,
        )
        vaga.status = StatusVaga.OCUPADA
        self.db.commit()
        self.db.refresh(alocacao)
        return AlocacaoResposta.model_validate(alocacao)

    def liberar_alocacao(self, voo_id: int, alocacao_id: int) -> AlocacaoResposta:
        self.obter_model(voo_id)
        alocacao = self.alocacao_repo.buscar(alocacao_id)
        if alocacao is None or alocacao.voo_id != voo_id:
            raise NaoEncontrado(f"Alocação {alocacao_id} não encontrada para o voo {voo_id}.")
        if not alocacao.ativa:
            raise Conflito("Esta alocação já foi liberada.")
        alocacao.ativa = False
        alocacao.fim = datetime.now()
        alocacao.vaga.status = StatusVaga.LIVRE
        self.db.commit()
        self.db.refresh(alocacao)
        return AlocacaoResposta.model_validate(alocacao)
