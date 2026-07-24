"""Exceções de domínio traduzidas em respostas HTTP por src/middlewares/erros.py."""


class AppError(Exception):
    """Erro de aplicação com status HTTP e código legível."""

    status_code = 400
    codigo = "ERRO"

    def __init__(self, detail: str, codigo: str | None = None):
        self.detail = detail
        if codigo:
            self.codigo = codigo
        super().__init__(detail)


class NaoEncontrado(AppError):
    """Recurso inexistente."""

    status_code = 404
    codigo = "NAO_ENCONTRADO"


class RegraDeNegocio(AppError):
    """Operação recusada por uma regra do domínio."""

    status_code = 422
    codigo = "REGRA_DE_NEGOCIO"


class Conflito(AppError):
    """Estado atual do recurso impede a operação (transição inválida, duplicidade, lotação)."""

    status_code = 409
    codigo = "CONFLITO"
