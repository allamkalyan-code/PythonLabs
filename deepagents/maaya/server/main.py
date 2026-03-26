"""FastAPI application entry point for Maaya v2."""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load .env from the Maaya project root (parent of server/)
load_dotenv(Path(__file__).parent.parent / ".env")

from server.database import init_db
from server.routers import agent as agent_router
from server.routers import projects as projects_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle handler."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to maaya/.env or export it before starting the server."
        )
        sys.exit(1)
    init_db()
    logger.info("Maaya v2 ready — database initialized")
    yield


app = FastAPI(title="Maaya v2", version="2.0.0", lifespan=lifespan)

# Allow the Vite dev server to connect during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router.router)
app.include_router(agent_router.router)

# Serve the built React app for all non-API routes
_STATIC_DIR = Path(__file__).parent.parent / "frontend" / "dist"
if _STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
else:
    logger.warning(
        "Frontend build not found at %s — run `npm run build` inside frontend/",
        _STATIC_DIR,
    )



def run() -> None:
    """Entry point for `uv run python -m server.main`."""
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    run()
