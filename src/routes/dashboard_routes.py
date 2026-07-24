from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.dashboard import ResumoDashboard
from src.use_cases.dashboard_use_case import DashboardUseCase

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/resumo", response_model=ResumoDashboard)
def resumo(db: Session = Depends(get_db)):
    return DashboardUseCase(db).resumo()
