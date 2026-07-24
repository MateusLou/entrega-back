from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.bagagem import BagagemAtualizarStatus, BagagemCriar, BagagemResposta
from src.use_cases.bagagem_use_case import BagagemUseCase
from src.utils.enums import StatusBagagem

router = APIRouter(prefix="/bagagens", tags=["Bagagens"])


@router.get("", response_model=list[BagagemResposta])
def listar(
    status_bagagem: StatusBagagem | None = Query(default=None, alias="status"),
    reserva_id: int | None = Query(default=None),
    voo_id: int | None = Query(default=None),
    passageiro_id: int | None = Query(default=None),
    etiqueta: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return BagagemUseCase(db).listar(
        status=status_bagagem,
        reserva_id=reserva_id,
        voo_id=voo_id,
        passageiro_id=passageiro_id,
        etiqueta=etiqueta,
    )


@router.get("/rastreio/{etiqueta}", response_model=BagagemResposta)
def rastrear(etiqueta: str, db: Session = Depends(get_db)):
    return BagagemUseCase(db).rastrear(etiqueta)


@router.get("/{bagagem_id}", response_model=BagagemResposta)
def obter(bagagem_id: int, db: Session = Depends(get_db)):
    return BagagemUseCase(db).obter(bagagem_id)


@router.post("", response_model=BagagemResposta, status_code=status.HTTP_201_CREATED)
def despachar(dados: BagagemCriar, db: Session = Depends(get_db)):
    return BagagemUseCase(db).despachar(dados)


@router.patch("/{bagagem_id}/status", response_model=BagagemResposta)
def alterar_status(
    bagagem_id: int, dados: BagagemAtualizarStatus, db: Session = Depends(get_db)
):
    return BagagemUseCase(db).alterar_status(bagagem_id, dados)


@router.delete("/{bagagem_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(bagagem_id: int, db: Session = Depends(get_db)):
    BagagemUseCase(db).remover(bagagem_id)
