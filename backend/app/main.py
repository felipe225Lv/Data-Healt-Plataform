"""Punto de entrada de la API de Data Health Platform."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.container import Container
from app.core.exceptions import DomainError

logging.basicConfig(level=logging.INFO)


def create_app(seed: bool = True) -> FastAPI:
    app = FastAPI(
        title="Data Health Platform API",
        version="1.0.0",
        description="Observabilidad y alertas de calidad de datos para pymes",
    )
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    container = Container()
    if seed:
        container.seed()
    app.state.container = container

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    app.include_router(router)
    return app


app = create_app()
