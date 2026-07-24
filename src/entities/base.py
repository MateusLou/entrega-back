from pydantic import BaseModel, ConfigDict


class Esquema(BaseModel):
    """Base dos schemas de resposta: permite construir a partir dos models ORM."""

    model_config = ConfigDict(from_attributes=True)
