from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.aeronave import AeronaveAtualizar, AeronaveCriar, AeronaveResposta
from src.entities.voo import VooResposta
from src.use_cases.aeronave_use_case import AeronaveUseCase
from src.use_cases.voo_use_case import VooUseCase

router = APIRouter(prefix="/aeronaves", tags=["Aeronaves"])


@router.get("", response_model=list[AeronaveResposta])
def listar(db: Session = Depends(get_db)):
    return AeronaveUseCase(db).listar()


@router.get("/{aeronave_id}", response_model=AeronaveResposta)
def obter(aeronave_id: int, db: Session = Depends(get_db)):
    return AeronaveUseCase(db).obter(aeronave_id)


@router.get("/{aeronave_id}/voos", response_model=list[VooResposta])
def listar_voos(aeronave_id: int, db: Session = Depends(get_db)):
    AeronaveUseCase(db).obter_model(aeronave_id)
    return VooUseCase(db).listar(aeronave_id=aeronave_id)


@router.post("", response_model=AeronaveResposta, status_code=status.HTTP_201_CREATED)
def criar(dados: AeronaveCriar, db: Session = Depends(get_db)):
    return AeronaveUseCase(db).criar(dados)


@router.put("/{aeronave_id}", response_model=AeronaveResposta)
def atualizar(aeronave_id: int, dados: AeronaveAtualizar, db: Session = Depends(get_db)):
    return AeronaveUseCase(db).atualizar(aeronave_id, dados)


@router.delete("/{aeronave_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(aeronave_id: int, db: Session = Depends(get_db)):
    AeronaveUseCase(db).remover(aeronave_id)
