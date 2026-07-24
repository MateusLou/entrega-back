from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.bagagem import BagagemResposta
from src.entities.reserva import RealocarReserva, ReservaCriar, ReservaResposta
from src.use_cases.bagagem_use_case import BagagemUseCase
from src.use_cases.reserva_use_case import ReservaUseCase
from src.utils.enums import StatusReserva

router = APIRouter(prefix="/reservas", tags=["Reservas"])


@router.get("", response_model=list[ReservaResposta])
def listar(
    voo_id: int | None = Query(default=None),
    passageiro_id: int | None = Query(default=None),
    status_reserva: StatusReserva | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    return ReservaUseCase(db).listar(voo_id, passageiro_id, status_reserva)


@router.get("/{reserva_id}", response_model=ReservaResposta)
def obter(reserva_id: int, db: Session = Depends(get_db)):
    return ReservaUseCase(db).obter(reserva_id)


@router.get("/{reserva_id}/bagagens", response_model=list[BagagemResposta])
def bagagens(reserva_id: int, db: Session = Depends(get_db)):
    ReservaUseCase(db).obter_model(reserva_id)
    return BagagemUseCase(db).listar(reserva_id=reserva_id)


@router.post("", response_model=ReservaResposta, status_code=status.HTTP_201_CREATED)
def criar(dados: ReservaCriar, db: Session = Depends(get_db)):
    return ReservaUseCase(db).criar(dados)


@router.patch("/{reserva_id}/check-in", response_model=ReservaResposta)
def check_in(reserva_id: int, db: Session = Depends(get_db)):
    return ReservaUseCase(db).check_in(reserva_id)


@router.patch("/{reserva_id}/no-show", response_model=ReservaResposta)
def no_show(reserva_id: int, db: Session = Depends(get_db)):
    return ReservaUseCase(db).no_show(reserva_id)


@router.post("/{reserva_id}/realocar", response_model=ReservaResposta)
def realocar(reserva_id: int, dados: RealocarReserva, db: Session = Depends(get_db)):
    return ReservaUseCase(db).realocar(reserva_id, dados)


@router.delete("/{reserva_id}", response_model=ReservaResposta)
def cancelar(reserva_id: int, db: Session = Depends(get_db)):
    return ReservaUseCase(db).cancelar(reserva_id)
