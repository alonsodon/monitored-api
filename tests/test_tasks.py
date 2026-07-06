# tests/test_tasks.py
from unittest.mock import patch

import pytest


class TestCreateTask:
    def test_success(self, client):
        response = client.post("/tasks", json={"title": "Learn Testing"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Learn Testing"
        assert data["done"] is False
        assert "id" in data

    @pytest.mark.parametrize(
        "title,expected_status",
        [
            ("Valid title", 201),
            ("", 422),
            ("   ", 422),
            ("A" * 200, 201),
            ("A" * 201, 422),  # AAA...A
        ],
    )
    def test_title_validation(self, client, title, expected_status):
        response = client.post("/tasks", json={"title": title})
        assert response.status_code == expected_status


class TestGetTask:
    def test_existing(self, client, sample_task):
        response = client.get(f"/tasks/{sample_task.id}")
        assert response.status_code == 200
        assert response.json()["id"] == sample_task.id


class TestGetTaskList:
    def test_existing_list(self, client, sample_task):
        response = client.get("/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_task.id
        assert data[0]["title"] == sample_task.title

    def test_empty(self, client):
        response = client.get("/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_limit(self, client, db_session):
        from app.models import Task

        for i in range(5):
            db_session.add(Task(title=f"Task {i}"))
        db_session.commit()
        response = client.get("/tasks?limit=3")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_skip(self, client, db_session):
        from app.models import Task

        tasks = [Task(title=f"Task {i}") for i in range(5)]
        for t in tasks:
            db_session.add(t)
        db_session.commit()
        for t in tasks:
            db_session.refresh(t)  # obtener ids asignados
        skipped_ids = {tasks[0].id, tasks[1].id, tasks[2].id}

        response = client.get("/tasks?skip=3&limit=10")
        assert response.status_code == 200
        returned = response.json()
        assert len(returned) == 2  # 5 - 3

        """Comprobar que verdaderamente no haya ninguna de las tareas del skip"""
        returned_ids = [t["id"] for t in returned]
        assert skipped_ids.isdisjoint(returned_ids)  # ninguno de los saltados aparece

    @pytest.mark.parametrize(
        "limit,expected_status",
        [
            (20, 200),
            (100, 200),  # boundary testing
            (101, 400),  # limit = 101
        ],
    )
    def test_limit_validation(self, client, limit, expected_status):
        response = client.get(f"/tasks?limit={limit}")
        assert response.status_code == expected_status


class TestUpdateTask:
    @patch("app.services.requests.post")
    def test_mark_done(self, mock_post, client, sample_task):
        mock_post.return_value.status_code = 200
        response = client.patch(f"/tasks/{sample_task.id}", json={"done": True})
        assert response.status_code == 200
        assert response.json()["done"] is True


class TestDeleteTask:
    def test_delete(self, client, sample_task, db_session):
        from app.models import Task

        response = client.delete(f"/tasks/{sample_task.id}")
        assert response.status_code == 204
        # comprueba en la BD que de verdad ya no está
        en_db = db_session.query(Task).filter(Task.id == sample_task.id).first()
        assert en_db is None


class TestNotFound:
    def test_get_not_found(self, client):
        assert client.get("/tasks/99999").status_code == 404

    def test_delete_not_found(self, client):
        assert client.delete("/tasks/99999").status_code == 404

    def test_patch_not_found(self, client):
        assert client.patch("/tasks/99999", json={"done": True}).status_code == 404


class TestNotifications:
    @patch("app.services.requests.post")
    def test_sends_notification_on_completion(self, mock_post, client, sample_task):
        mock_post.return_value.status_code = 200
        response = client.patch(f"/tasks/{sample_task.id}", json={"done": True})
        assert response.status_code == 200
        mock_post.assert_called_once()
