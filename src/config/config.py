from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    # extra="ignore": variáveis a mais no .env (de versões anteriores, por exemplo)
    # são ignoradas em vez de derrubar a aplicação no import.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings():
    return Settings()
