# app/metrics.py

from prometheus_client import Counter, Histogram

# Técnicas (salud del sistema)
REQUEST_COUNT = Counter(
    "app_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],  # labels: dimesiones para filtrar
)
REQUEST_LATENCY = Histogram(
    "app_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

# De negocio
TASKS_CREATED = Counter("app_tasks_created_total", "Total tasks created")
TASKS_COMPLETED = Counter("app_tasks_completed_total", "Total tasks completed")
