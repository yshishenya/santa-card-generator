"""Endpoint tests for the protected print archive API."""

from fastapi.testclient import TestClient

from src.api import dependencies
from src.config import settings
from src.main import app


def test_print_archive_auth_and_empty_list(tmp_path) -> None:
    original_storage_path = settings.print_archive_storage_path
    object.__setattr__(settings, "print_archive_storage_path", str(tmp_path / "print-archive"))
    dependencies._print_archive_store = None

    try:
        client = TestClient(app)

        status_response = client.get("/api/v1/print-assets/auth/status")
        assert status_response.status_code == 200
        assert status_response.json()["data"]["authenticated"] is False

        verify_response = client.post(
            "/api/v1/print-assets/auth/verify",
            json={"password": settings.print_archive_password},
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["data"]["authenticated"] is True

        assets_response = client.get("/api/v1/print-assets/assets")
        assert assets_response.status_code == 200
        assert assets_response.json()["data"]["assets"] == []
    finally:
        object.__setattr__(settings, "print_archive_storage_path", original_storage_path)
        dependencies._print_archive_store = None


def test_print_archive_assets_requires_authentication() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/print-assets/assets")

    assert response.status_code == 401
    assert response.json()["detail"] == "Print archive authentication required"
