from sqlalchemy import func

from src.models.aeronave import Aeronave
from src.models.voo import Voo
from src.repositories.base_repository import BaseRepository


class AeronaveRepository(BaseRepository[Aeronave]):
    model = Aeronave

    def buscar_por_prefixo(self, prefixo: str) -> Aeronave | None:
        return self.db.query(Aeronave).filter(Aeronave.prefixo == prefixo).first()

    def contar_voos(self) -> dict[int, int]:
        linhas = (
            self.db.query(Voo.aeronave_id, func.count(Voo.id)).group_by(Voo.aeronave_id).all()
        )
        return {aid: int(total) for aid, total in linhas}
