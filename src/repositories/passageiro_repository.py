from sqlalchemy import func, or_

from src.models.passageiro import Passageiro
from src.repositories.base_repository import BaseRepository


class PassageiroRepository(BaseRepository[Passageiro]):
    model = Passageiro

    def listar_filtrado(self, busca: str | None = None) -> list[Passageiro]:
        consulta = self.db.query(Passageiro)
        if busca:
            alvo = f"%{busca}%"
            consulta = consulta.filter(
                or_(Passageiro.nome.like(alvo), Passageiro.documento.like(alvo))
            )
        return list(consulta.order_by(Passageiro.nome).all())

    def buscar_por_documento(self, documento: str) -> Passageiro | None:
        return self.db.query(Passageiro).filter(Passageiro.documento == documento).first()

    def total(self) -> int:
        return int(self.db.query(func.count(Passageiro.id)).scalar() or 0)
