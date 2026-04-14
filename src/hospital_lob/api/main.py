"""FastAPI application for Hospital LOB."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hospital_lob.data.store import get_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_store()
    yield


app = FastAPI(
    title="Hospital LOB API",
    description="Line of Balance framework for hospital operations",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from hospital_lob.api.routes import alerts, bottlenecks, chat, data, metrics, pharmacy, simulation  # noqa: E402

app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(bottlenecks.router, prefix="/api", tags=["bottlenecks"])
app.include_router(simulation.router, prefix="/api", tags=["simulation"])
app.include_router(pharmacy.router, prefix="/api/pharmacy", tags=["pharmacy"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
