"""FastAPI app factory. One container runs Next.js + FastAPI (ticket 07); the
frontend rewrites /api/* here. DB lives in /data (or an injected path)."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_settings
from .db import connect, init_db
from .routers import auth, close, forecast, months, settings as settings_router, shares, slips, sources
from .services import fx

log = logging.getLogger(__name__)

POLL_INTERVAL = 60 * 60  # hourly poll (ticket 08: source refreshes ~24h)


async def _fx_poll_loop(app: FastAPI) -> None:
    while True:
        try:
            conn = connect(app.state.db_path)
            try:
                await fx.refresh_snapshot(conn)
            finally:
                conn.close()
        except Exception:  # never let the poll kill the app
            log.exception("fx poll failed")
        await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = connect(app.state.db_path)
    init_db(conn)
    conn.close()
    if app.state.fx_poll:
        app.state.fx_task = asyncio.create_task(_fx_poll_loop(app))
    yield
    if getattr(app.state, "fx_task", None):
        app.state.fx_task.cancel()


def create_app(db_path: str | None = None, fx_poll: bool = True) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Salary Tracker API", lifespan=lifespan)
    app.state.db_path = db_path or (settings.data_dir.rstrip("/") + "/salary.db")
    app.state.fx_poll = fx_poll

    app.include_router(auth.router)
    app.include_router(settings_router.router)
    app.include_router(sources.router)
    app.include_router(close.router)
    app.include_router(forecast.router)
    app.include_router(months.router)
    app.include_router(shares.router)
    app.include_router(slips.router)

    @app.get("/api/health")
    def health():
        return {"ok": True}

    return app


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:create_app", factory=True, host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    main()
