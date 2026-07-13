# app/main.py
import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.metrics import REQUEST_COUNT, REQUEST_LATENCY
from app.routers import tasks

app = FastAPI(
    title="Monitored API",
    description="A production-grade REST API demonstrating FastAPI + PostgreSQL + Docker + Terraform + Prometheus/Grafana",
    version="1.0.0",
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)  # deja pasar la request al endpoint
    duration = time.time() - start

    route = request.scope.get("route")
    endpoint = route.path if route else request.url.path

    if endpoint != "/metrics":
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
        ).inc()

        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

    return response


app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


@app.get("/metrics", tags=["system"])
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
