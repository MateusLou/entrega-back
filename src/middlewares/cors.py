from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ORIGENS_PERMITIDAS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]


def configurar_cors(app: FastAPI) -> None:
    """Libera o frontend Vite para consumir a API."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGENS_PERMITIDAS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
