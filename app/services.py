# app/services.py
import requests


def send_notification(task_title: str) -> None:
    """Avisa a un servicio externo de que una tarea se completó."""
    requests.post(
        "https://example.com/notify",
        json={"message": f"Tarea completada: {task_title}"},
        timeout=5,
    )
