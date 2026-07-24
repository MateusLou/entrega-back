from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.terminal import TerminalAtualizar, TerminalCriar, TerminalResposta
from src.entities.vaga import VagaResposta
from src.use_cases.terminal_use_case import TerminalUseCase
from src.use_cases.vaga_use_case import VagaUseCase

router = APIRouter(prefix="/terminais", tags=["Terminais"])


@router.get("", response_model=list[TerminalResposta])
def listar(db: Session = Depends(get_db)):
    return TerminalUseCase(db).listar()


@router.get("/{terminal_id}", response_model=TerminalResposta)
def obter(terminal_id: int, db: Session = Depends(get_db)):
    return TerminalUseCase(db).obter(terminal_id)


@router.get("/{terminal_id}/vagas", response_model=list[VagaResposta])
def listar_vagas(terminal_id: int, db: Session = Depends(get_db)):
    TerminalUseCase(db).obter_model(terminal_id)
    return VagaUseCase(db).listar(terminal_id=terminal_id)


@router.post("", response_model=TerminalResposta, status_code=status.HTTP_201_CREATED)
def criar(dados: TerminalCriar, db: Session = Depends(get_db)):
    return TerminalUseCase(db).criar(dados)


@router.put("/{terminal_id}", response_model=TerminalResposta)
def atualizar(terminal_id: int, dados: TerminalAtualizar, db: Session = Depends(get_db)):
    return TerminalUseCase(db).atualizar(terminal_id, dados)


@router.delete("/{terminal_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(terminal_id: int, db: Session = Depends(get_db)):
    TerminalUseCase(db).remover(terminal_id)
