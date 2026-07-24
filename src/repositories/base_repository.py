from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from src.database.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """CRUD genérico. Cada repositório concreto define o model e acrescenta consultas."""

    model: type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def listar(self) -> list[ModelT]:
        return list(self.db.query(self.model).order_by(self.model.id).all())

    def buscar(self, id_: int) -> ModelT | None:
        return self.db.get(self.model, id_)

    def criar(self, **dados) -> ModelT:
        obj = self.model(**dados)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def atualizar(self, obj: ModelT, **dados) -> ModelT:
        for campo, valor in dados.items():
            setattr(obj, campo, valor)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def remover(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.commit()
