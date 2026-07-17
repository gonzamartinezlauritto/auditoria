from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.logger import logger
from app.exceptions.base import AppException


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    logger.warning(
        "Error de aplicación: code=%s path=%s message=%s",
        exc.code,
        request.url.path,
        exc.message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        },
    )