import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.exceptions import AppException


def _build_error_payload(
    error: str,
    message: str,
    path: str,
    details: list[dict] | None = None,
) -> dict:
    return {
        "error": error,
        "message": message,
        "details": details or [],
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "path": path,
        "requestId": str(uuid.uuid4()),
    }


def registrar_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        payload = _build_error_payload(
            error=exc.error,
            message=exc.message,
            path=request.url.path,
            details=exc.details,
        )
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        details = []
        for err in exc.errors():
            loc = [str(item) for item in err.get("loc", []) if item != "body"]
            field = ".".join(loc) if loc else "request"
            details.append({"field": field, "issue": err.get("msg", "Valor inválido")})

        payload = _build_error_payload(
            error="DADOS_INVALIDOS",
            message="Erro de validação nos dados enviados.",
            path=request.url.path,
            details=details,
        )
        return JSONResponse(status_code=422, content=payload)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        payload = _build_error_payload(
            error=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            path=request.url.path,
        )
        return JSONResponse(status_code=exc.status_code, content=payload)