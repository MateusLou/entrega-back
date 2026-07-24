from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.alocacao import AlocacaoCriar, AlocacaoResposta
from src.entities.bagagem import BagagemResposta
from src.entities.reserva import ReservaResposta
from src.entities.voo import (
    AlterarStatusVoo,
    OcupacaoVoo,
    VooAtualizar,
    VooCriar,
    VooResposta,
)
from src.use_cases.bagagem_use_case import BagagemUseCase
from src.use_cases.reserva_use_case import ReservaUseCase
from src.use_cases.voo_use_case import VooUseCase
from src.utils.enums import SentidoVoo, StatusVoo

router = APIRouter(prefix="/voos", tags=["Voos"])


@router.get("", response_model=list[VooResposta])
def listar(
    status_voo: StatusVoo | None = Query(default=None, alias="status"),
    terminal_id: int | None = Query(default=None),
    aeronave_id: int | None = Query(default=None),
    origem: str | None = Query(default=None, max_length=3),
    destino: str | None = Query(default=None, max_length=3),
    data: date | None = Query(default=None),
    sentido: SentidoVoo | None = Query(default=None),
    busca: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return VooUseCase(db).listar(
        status=status_voo,
        terminal_id=terminal_id,
        aeronave_id=aeronave_id,
        origem=origem,
        destino=destino,
        data=data,
        sentido=sentido,
        busca=busca,
    )


@router.get("/{voo_id}", response_model=VooResposta)
def obter(voo_id: int, db: Session = Depends(get_db)):
    return VooUseCase(db).obter(voo_id)


@router.get("/{voo_id}/ocupacao", response_model=OcupacaoVoo)
def ocupacao(voo_id: int, db: Session = Depends(get_db)):
    return VooUseCase(db).ocupacao(voo_id)


@router.get("/{voo_id}/passageiros", response_model=list[ReservaResposta])
def manifesto(voo_id: int, db: Session = Depends(get_db)):
    VooUseCase(db).obter_model(voo_id)
    return ReservaUseCase(db).listar(voo_id=voo_id)


@router.get("/{voo_id}/bagagens", response_model=list[BagagemResposta])
def bagagens(voo_id: int, db: Session = Depends(get_db)):
    VooUseCase(db).obter_model(voo_id)
    return BagagemUseCase(db).listar(voo_id=voo_id)


@router.get("/{voo_id}/alocacoes", response_model=list[AlocacaoResposta])
def listar_alocacoes(voo_id: int, db: Session = Depends(get_db)):
    return VooUseCase(db).listar_alocacoes(voo_id)


@router.post("", response_model=VooResposta, status_code=status.HTTP_201_CREATED)
def criar(dados: VooCriar, db: Session = Depends(get_db)):
    return VooUseCase(db).criar(dados)


@router.put("/{voo_id}", response_model=VooResposta)
def atualizar(voo_id: int, dados: VooAtualizar, db: Session = Depends(get_db)):
    return VooUseCase(db).atualizar(voo_id, dados)


@router.patch("/{voo_id}/status", response_model=VooResposta)
def alterar_status(voo_id: int, dados: AlterarStatusVoo, db: Session = Depends(get_db)):
    return VooUseCase(db).alterar_status(voo_id, dados.status)


@router.post(
    "/{voo_id}/alocacoes",
    response_model=AlocacaoResposta,
    status_code=status.HTTP_201_CREATED,
)
def alocar_vaga(voo_id: int, dados: AlocacaoCriar, db: Session = Depends(get_db)):
    return VooUseCase(db).alocar_vaga(voo_id, dados)


@router.patch("/{voo_id}/alocacoes/{alocacao_id}/liberar", response_model=AlocacaoResposta)
def liberar_alocacao(voo_id: int, alocacao_id: int, db: Session = Depends(get_db)):
    return VooUseCase(db).liberar_alocacao(voo_id, alocacao_id)


@router.delete("/{voo_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(voo_id: int, db: Session = Depends(get_db)):
    VooUseCase(db).remover(voo_id)
