import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from src.utils.exceptions import AppError

logger = logging.getLogger("aeroporto")


def configurar_tratamento_de_erros(app: FastAPI) -> None:
    """Converte exceções de domínio em respostas JSON padronizadas."""

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "codigo": exc.codigo},
        )

    @app.exception_handler(IntegrityError)
    async def _integridade(_: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("Violação de integridade no banco: %s", exc)
        return JSONResponse(
            status_code=409,
            content={
                "detail": "A operação viola uma restrição de integridade do banco de dados.",
                "codigo": "INTEGRIDADE",
            },
        )
