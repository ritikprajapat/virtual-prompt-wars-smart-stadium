"""FastAPI application entrypoint: the create_app factory and startup wiring.

The app is assembled by ``create_app`` so its dependencies — settings, the
venue data, the LLM client, and the crowd simulator — are wired once and
exposed on ``app.state`` rather than reached for as module-level globals.
Routes read those collaborators from ``request.app.state``, which keeps the
composition root in one place and the request handlers dependency-injected.
"""
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.middleware.rate_limiter import limiter
from app.routes import accessibility, crowd, sustainability, transport, wayfinding
from app.services.crowd import simulator
from app.services.llm import get_llm_client
from app.services.repository import JsonVenueRepository, VenueRepository

templates = Jinja2Templates(directory="app/templates")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start the crowd simulation loop on startup and stop it on shutdown."""
    app.state.simulator.start_background_loop()
    yield
    app.state.simulator.stop_background_loop()


async def security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Attach hardening headers to every response and disable static caching."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; connect-src 'self'"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


async def validation_exception_handler(
    _request: Request, _exc: RequestValidationError
) -> JSONResponse:
    """Return a generic 422 so raw validation details never reach the client."""
    return JSONResponse(status_code=422, content={"detail": "Invalid request"})


async def index(request: Request) -> Response:
    """Render the fan-facing assistant landing page."""
    venue = request.app.state.venue
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "gates": venue.gates,
            "sections": venue.sections,
            "facilities": venue.facilities,
        },
    )


async def dashboard(request: Request) -> Response:
    """Render the staff-facing live operations dashboard."""
    venue = request.app.state.venue
    return templates.TemplateResponse(request, "dashboard.html", {"gates": venue.gates})


def create_app(
    settings: Settings | None = None,
    venue_repository: VenueRepository | None = None,
) -> FastAPI:
    """Build and wire a MatchDay AI application instance.

    All shared collaborators are constructed here (the composition root) and
    stored on ``app.state`` so handlers depend on abstractions passed in via
    ``request.app.state`` rather than importing concrete module-level globals.
    ``venue_repository`` defaults to the file-backed :class:`JsonVenueRepository`
    but any :class:`VenueRepository` can be injected (e.g. an in-memory one in
    tests) without changing a single handler.
    """
    settings = settings or get_settings()
    venue_repository = venue_repository or JsonVenueRepository()

    app = FastAPI(title="MatchDay AI", lifespan=lifespan)

    app.state.limiter = limiter
    app.state.venue_repository = venue_repository
    app.state.venue = venue_repository.load_venue()
    app.state.llm = get_llm_client(settings)
    app.state.simulator = simulator

    # slowapi's handler signature is narrower than Starlette's generic Exception
    # handler type, but is correct for the RateLimitExceeded it is registered
    # against.
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.exception_handler(RequestValidationError)(validation_exception_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.middleware("http")(security_headers)

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    app.include_router(wayfinding.router)
    app.include_router(crowd.router)
    app.include_router(accessibility.router)
    app.include_router(transport.router)
    app.include_router(sustainability.router)

    app.get("/")(index)
    app.get("/dashboard")(dashboard)

    return app


app = create_app()
