from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

#: Portas do Vite em desenvolvimento (5173 e as seguintes, quando a 5173 está
#: ocupada) e a do `vite preview` (4173).
ORIGENS_PERMITIDAS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
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
