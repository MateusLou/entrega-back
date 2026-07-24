from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from src.entities.base import Esquema


class PassageiroCriar(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    documento: str = Field(min_length=3, max_length=30)
    email: EmailStr | None = None
    telefone: str | None = Field(default=None, max_length=30)


class PassageiroAtualizar(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    documento: str | None = Field(default=None, min_length=3, max_length=30)
    email: EmailStr | None = None
    telefone: str | None = Field(default=None, max_length=30)


class PassageiroResumo(Esquema):
    id: int
    nome: str
    documento: str


class PassageiroResposta(PassageiroResumo):
    email: str | None = None
    telefone: str | None = None
    criado_em: datetime
    total_reservas: int = 0
