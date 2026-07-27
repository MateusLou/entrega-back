from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
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
from src.utils.notificacoes import notificar_passageiro_criado

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
def criar(dados: PassageiroCriar, tarefas: BackgroundTasks, db: Session = Depends(get_db)):
    passageiro = PassageiroUseCase(db).criar(dados)
    # Depois da resposta sair: quem cadastrou não espera pelo n8n, e uma falha lá
    # não afeta o 201. O use case segue sem efeito colateral externo, então o
    # src/seed.py, que o chama direto, não dispara notificação.
    tarefas.add_task(notificar_passageiro_criado, passageiro.model_dump(mode="json"))
    return passageiro


@router.put("/{passageiro_id}", response_model=PassageiroResposta)
def atualizar(passageiro_id: int, dados: PassageiroAtualizar, db: Session = Depends(get_db)):
    return PassageiroUseCase(db).atualizar(passageiro_id, dados)


@router.delete("/{passageiro_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(passageiro_id: int, db: Session = Depends(get_db)):
    PassageiroUseCase(db).remover(passageiro_id)
