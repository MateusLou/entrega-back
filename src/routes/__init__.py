from fastapi import APIRouter

from src.routes import (
    aeronave_routes,
    bagagem_routes,
    dashboard_routes,
    passageiro_routes,
    reserva_routes,
    terminal_routes,
    vaga_routes,
    voo_routes,
)

api_router = APIRouter(prefix="/api")


@api_router.get("/health", tags=["Infra"])
def health():
    return {"status": "ok"}


api_router.include_router(dashboard_routes.router)
api_router.include_router(terminal_routes.router)
api_router.include_router(vaga_routes.router)
api_router.include_router(aeronave_routes.router)
api_router.include_router(voo_routes.router)
api_router.include_router(passageiro_routes.router)
api_router.include_router(reserva_routes.router)
api_router.include_router(bagagem_routes.router)
