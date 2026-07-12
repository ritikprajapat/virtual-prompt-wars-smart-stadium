"""FastAPI application entrypoint: routing, middleware, and startup wiring."""
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

from app.config import get_settings
from app.middleware.rate_limiter import limiter
from app.routes import accessibility, crowd, sustainability, transport, wayfinding
from app.services.crowd import simulator
from app.services.venue_repository import load_venue


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Start the crowd simulation loop on startup and stop it on shutdown."""
    simulator.start_background_loop()
    yield
    simulator.stop_background_loop()


app = FastAPI(title="MatchDay AI", lifespan=lifespan)
app.state.limiter = limiter
# slowapi's handler signature is narrower than Starlette's generic Exception
# handler type, but is correct for the RateLimitExceeded it is registered against.
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(wayfinding.router)
app.include_router(crowd.router)
app.include_router(accessibility.router)
app.include_router(transport.router)
app.include_router(sustainability.router)


@app.middleware("http")
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, _exc: RequestValidationError
) -> JSONResponse:
    """Return a generic 422 so raw validation details never reach the client."""
    return JSONResponse(status_code=422, content={"detail": "Invalid request"})


@app.get("/")
async def index(request: Request) -> Response:
    """Render the fan-facing assistant landing page."""
    venue = load_venue()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "gates": venue.gates,
            "sections": venue.sections,
            "facilities": venue.facilities,
        },
    )


@app.get("/dashboard")
async def dashboard(request: Request) -> Response:
    """Render the staff-facing live operations dashboard."""
    venue = load_venue()
    return templates.TemplateResponse(request, "dashboard.html", {"gates": venue.gates})
