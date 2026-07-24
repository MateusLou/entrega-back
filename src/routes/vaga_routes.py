from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.vaga import VagaAtualizar, VagaCriar, VagaResposta
from src.use_cases.vaga_use_case import VagaUseCase
from src.utils.enums import StatusVaga, TipoVaga

router = APIRouter(prefix="/vagas", tags=["Vagas / Gates"])


@router.get("", response_model=list[VagaResposta])
def listar(
    terminal_id: int | None = Query(default=None),
    status_vaga: StatusVaga | None = Query(default=None, alias="status"),
    tipo: TipoVaga | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return VagaUseCase(db).listar(terminal_id=terminal_id, status=status_vaga, tipo=tipo)


@router.get("/{vaga_id}", response_model=VagaResposta)
def obter(vaga_id: int, db: Session = Depends(get_db)):
    return VagaUseCase(db).obter(vaga_id)


@router.post("", response_model=VagaResposta, status_code=status.HTTP_201_CREATED)
def criar(dados: VagaCriar, db: Session = Depends(get_db)):
    return VagaUseCase(db).criar(dados)


@router.put("/{vaga_id}", response_model=VagaResposta)
def atualizar(vaga_id: int, dados: VagaAtualizar, db: Session = Depends(get_db)):
    return VagaUseCase(db).atualizar(vaga_id, dados)


@router.delete("/{vaga_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(vaga_id: int, db: Session = Depends(get_db)):
    VagaUseCase(db).remover(vaga_id)
