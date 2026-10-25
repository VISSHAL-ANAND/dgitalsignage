import os
import tempfile
import sys
from pathlib import Path

os.environ.setdefault("ADMIN_USER", "test-admin")
os.environ.setdefault("ADMIN_PASSWORD", "test-password-for-ci-only")
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="kids-signage-tests-")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
import app as signage

client = TestClient(signage.app)
ADMIN = (os.environ["ADMIN_USER"], os.environ["ADMIN_PASSWORD"])


def test_health_is_public():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_admin_api_requires_authentication():
    response = client.get("/api/admin/displays")
    assert response.status_code == 401


def test_display_create_upload_and_player_playlist():
    with client:
        created = client.post(
            "/api/admin/displays",
            auth=ADMIN,
            json={"id": "innovation-zone", "name": "Innovation Zone"},
        )
        assert created.status_code == 201

        # Small PNG signature/content fixture; upload handling currently validates extension and size.
        png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
            b"\x1f\x15\xc4\x89\x00\x00\x00\x0bIDAT\x08\xd7c\xf8\xcf\xc0"
            b"\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB\x60\x82"
        )
        uploaded = client.post(
            "/api/admin/upload",
            auth=ADMIN,
            data={"display_id": "innovation-zone", "duration": "5"},
            files={"file": ("lab-poster.png", png, "image/png")},
        )
        assert uploaded.status_code == 201, uploaded.text
        assert uploaded.json()["uploaded"] == 1

        playlist = client.get("/api/player/innovation-zone")
        assert playlist.status_code == 200
        payload = playlist.json()
        assert payload["display"]["name"] == "Innovation Zone"
        assert len(payload["items"]) == 1
        assert payload["items"][0]["title"] == "lab-poster"
        media_response = client.get(payload["items"][0]["url"])
        assert media_response.status_code == 200

        # An unrelated display has an independent playlist.
        empty = client.get("/api/player/main")
        assert empty.status_code == 200
        assert empty.json()["items"] == []


def test_unknown_display_returns_404():
    response = client.get("/api/player/no-such-display")
    assert response.status_code == 404
