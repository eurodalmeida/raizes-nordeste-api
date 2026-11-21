class AppException(Exception):
    def __init__(
        self,
        error: str,
        message: str,
        status_code: int = 400,
        details: list[dict] | None = None,
    ):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class RecursoNaoEncontradoError(AppException):
    def __init__(self, message: str = "Recurso não encontrado.", details: list[dict] | None = None):
        super().__init__(
            error="RECURSO_NAO_ENCONTRADO",
            message=message,
            status_code=404,
            details=details,
        )


class EstoqueInsuficienteError(AppException):
    def __init__(self, message: str = "Estoque insuficiente para um ou mais itens.", details: list[dict] | None = None):
        super().__init__(
            error="ESTOQUE_INSUFICIENTE",
            message=message,
            status_code=409,
            details=details,
        )


class ConflitoNegocioError(AppException):
    def __init__(self, message: str = "Conflito de regra de negócio.", details: list[dict] | None = None):
        super().__init__(
            error="CONFLITO_NEGOCIO",
            message=message,
            status_code=409,
            details=details,
        )


class AcessoNegadoError(AppException):
    def __init__(self, message: str = "Acesso negado para este perfil.", details: list[dict] | None = None):
        super().__init__(
            error="ACESSO_NEGADO",
            message=message,
            status_code=403,
            details=details,
        )


class NaoAutenticadoError(AppException):
    def __init__(self, message: str = "Credenciais inválidas ou token ausente.", details: list[dict] | None = None):
        super().__init__(
            error="NAO_AUTENTICADO",
            message=message,
            status_code=401,
            details=details,
        )