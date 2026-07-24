from fastapi import FastAPI

from src.middlewares.cors import configurar_cors
from src.middlewares.erros import configurar_tratamento_de_erros
from src.routes import api_router

DESCRICAO = """
API REST da plataforma de gestão operacional do aeroporto de Cape Town.

Centraliza voos, aeronaves, terminais, vagas de estacionamento (gates),
passageiros, reservas e bagagens.
"""


def create_app() -> FastAPI:
    app = FastAPI(
        title="Plataforma de Gestão Operacional de Aeroporto",
        description=DESCRICAO,
        version="1.0.0",
    )
    configurar_cors(app)
    configurar_tratamento_de_erros(app)
    app.include_router(api_router)

    @app.get("/", tags=["Infra"])
    def raiz():
        return {
            "servico": "Plataforma de Gestão Operacional de Aeroporto",
            "documentacao": "/docs",
            "api": "/api",
        }

    return app


app = create_app()
