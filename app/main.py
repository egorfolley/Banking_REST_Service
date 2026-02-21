from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import init_db


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api/v1")

    frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
    if frontend_dir.exists():
        app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

        @app.get("/")
        def root():
            return FileResponse(frontend_dir / "index.html")

        @app.get("/app")
        def app_page():
            return FileResponse(frontend_dir / "app.html")

        @app.get("/accounts")
        def accounts_page():
            return FileResponse(frontend_dir / "accounts.html")

        @app.get("/transfers")
        def transfers_page():
            return FileResponse(frontend_dir / "transfers.html")

        @app.get("/cards")
        def cards_page():
            return FileResponse(frontend_dir / "cards.html")

        @app.get("/statements")
        def statements_page():
            return FileResponse(frontend_dir / "statements.html")

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    return app


app = create_app()
