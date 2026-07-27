from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    #: Webhook do n8n avisado a cada passageiro cadastrado. Sem a variável, a
    #: notificação vira no-op e a aplicação roda normalmente sem o n8n.
    N8N_WEBHOOK_URL: str | None = None

    # extra="ignore": variáveis a mais no .env (de versões anteriores, por exemplo)
    # são ignoradas em vez de derrubar a aplicação no import.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings():
    return Settings()
