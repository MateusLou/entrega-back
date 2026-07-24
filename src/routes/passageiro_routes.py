from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.bagagem import BagagemResposta
from src.entities.passageiro import (
    PassageiroAtualizar,
    PassageiroCriar,
    PassageiroResposta,
)
from src.entities.reserva import ReservaResposta
from src.use_cases.bagagem_use_case import BagagemUseCase
from src.use_cases.passageiro_use_case import PassageiroUseCase
from src.use_cases.reserva_use_case import ReservaUseCase

router = APIRouter(prefix="/passageiros", tags=["Passageiros"])


@router.get("", response_model=list[PassageiroResposta])
def listar(busca: str | None = Query(default=None), db: Session = Depends(get_db)):
    return PassageiroUseCase(db).listar(busca)


@router.get("/{passageiro_id}", response_model=PassageiroResposta)
def obter(passageiro_id: int, db: Session = Depends(get_db)):
    return PassageiroUseCase(db).obter(passageiro_id)


@router.get("/{passageiro_id}/reservas", response_model=list[ReservaResposta])
def listar_reservas(passageiro_id: int, db: Session = Depends(get_db)):
    PassageiroUseCase(db).obter_model(passageiro_id)
    return ReservaUseCase(db).listar(passageiro_id=passageiro_id)


@router.get("/{passageiro_id}/bagagens", response_model=list[BagagemResposta])
def listar_bagagens(passageiro_id: int, db: Session = Depends(get_db)):
    PassageiroUseCase(db).obter_model(passageiro_id)
    return BagagemUseCase(db).listar(passageiro_id=passageiro_id)


@router.post("", response_model=PassageiroResposta, status_code=status.HTTP_201_CREATED)
def criar(dados: PassageiroCriar, db: Session = Depends(get_db)):
    return PassageiroUseCase(db).criar(dados)


@router.put("/{passageiro_id}", response_model=PassageiroResposta)
def atualizar(passageiro_id: int, dados: PassageiroAtualizar, db: Session = Depends(get_db)):
    return PassageiroUseCase(db).atualizar(passageiro_id, dados)


@router.delete("/{passageiro_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(passageiro_id: int, db: Session = Depends(get_db)):
    PassageiroUseCase(db).remover(passageiro_id)
