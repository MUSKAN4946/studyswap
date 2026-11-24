"""Central error handling.

Every error response has the same shape:
    {"error": "<machine_code>", "message": "<readable reason>"}
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """An expected error that we raise on purpose (for example session_full)."""

    def __init__(self, status_code: int, error: str, message: str):
        self.status_code = status_code
        self.error = error
        self.message = message
        super().__init__(message)


def _error_response(status_code: int, error: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "message": message},
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attach all error handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return _error_response(exc.status_code, exc.error, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        if errors:
            first = errors[0]
            field = ".".join(str(part) for part in first["loc"] if part != "body")
            message = f"Invalid input for '{field}': {first['msg']}"
        else:
            message = "The request body is invalid."
        return _error_response(422, "validation_error", message)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException):
        return _error_response(exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        # Never return a 500 with an empty body.
        return _error_response(
            500, "internal_error", "Something went wrong on the server."
        )