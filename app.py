from __future__ import annotations

import hmac
import mimetypes
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import uuid
from urllib.parse import parse_qs, urlparse
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data")).resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "signage.db"
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "200")) * 1024 * 1024
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_VIDEO = {".mp4", ".webm", ".mov", ".m4v"}
ALLOWED_PRESENTATION = {".ppt", ".pptx"}
security = HTTPBasic()
app = FastAPI(title="KIDS LAB Digital Signage", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@contextmanager
def db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS displays (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS media (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            media_type TEXT NOT NULL CHECK(media_type IN ('image','video')),
            mime_type TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS playlist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_id TEXT NOT NULL REFERENCES displays(id) ON DELETE CASCADE,
            media_id TEXT NOT NULL REFERENCES media(id) ON DELETE CASCADE,
            position INTEGER NOT NULL DEFAULT 0,
            duration INTEGER NOT NULL DEFAULT 10,
            UNIQUE(display_id, media_id)
        );
        CREATE TABLE IF NOT EXISTS display_controls (
            display_id TEXT PRIMARY KEY REFERENCES displays(id) ON DELETE CASCADE,
            mode TEXT NOT NULL DEFAULT 'play' CHECK(mode IN ('play','freeze','break')),
            updated_at TEXT NOT NULL
        );
        """)
        conn.execute(
            "INSERT OR IGNORE INTO displays(id, name, created_at) VALUES (?, ?, ?)",
            ("main", "KIDS LAB Main Display", now()),
        )
        conn.execute(
            "INSERT OR IGNORE INTO display_controls(display_id, mode, updated_at) VALUES ('main','play',?)",
            (now(),),
        )


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.on_event("startup")
def startup() -> None:
    if not ADMIN_PASSWORD:
        raise RuntimeError("ADMIN_PASSWORD is required. Copy .env.example and configure it before starting.")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


def require_admin(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> str:
    user_ok = hmac.compare_digest(credentials.username.encode(), ADMIN_USER.encode())
    pass_ok = hmac.compare_digest(credentials.password.encode(), ADMIN_PASSWORD.encode())
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


Admin = Annotated[str, Depends(require_admin)]


class DisplayCreate(BaseModel):
    id: str = Field(min_length=2, max_length=40, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
    name: str = Field(min_length=1, max_length=100)


class PlaylistUpdate(BaseModel):
    media_ids: list[str] = Field(max_length=500)
    duration: int = Field(default=10, ge=3, le=600)


def row_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def safe_media_path(filename: str) -> Path:
    path = (UPLOAD_DIR / filename).resolve()
    if path.parent != UPLOAD_DIR.resolve():
        raise HTTPException(400, "Invalid media path")
    return path


async def save_upload(upload: UploadFile, target: Path) -> int:
    total = 0
    with target.open("wb") as out:
        while chunk := await upload.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                out.close()
                target.unlink(missing_ok=True)
                raise HTTPException(413, f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit")
            out.write(chunk)
    await upload.close()
    if total == 0:
        target.unlink(missing_ok=True)
        raise HTTPException(400, "Empty files are not accepted")
    return total


def create_media_record(title: str, filename: str, media_type: str, mime_type: str) -> str:
    media_id = uuid.uuid4().hex
    with db() as conn:
        conn.execute(
            "INSERT INTO media(id,title,filename,media_type,mime_type,created_at) VALUES(?,?,?,?,?,?)",
            (media_id, title, filename, media_type, mime_type, now()),
        )
    return media_id


def add_to_playlist(display_id: str, media_id: str, duration: int = 10) -> None:
    with db() as conn:
        display = conn.execute("SELECT id FROM displays WHERE id=?", (display_id,)).fetchone()
        if not display:
            raise HTTPException(404, "Display not found")
        pos = conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 AS p FROM playlist_items WHERE display_id=?",
            (display_id,),
        ).fetchone()["p"]
        conn.execute(
            "INSERT OR IGNORE INTO playlist_items(display_id,media_id,position,duration) VALUES(?,?,?,?)",
            (display_id, media_id, pos, duration),
        )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "kids-lab-signage"}


@app.get("/")
def home() -> dict:
    return {"service": "KIDS LAB Digital Signage", "admin": "/admin", "default_display": "/display/main"}


@app.get("/admin", response_class=HTMLResponse)
def admin_page(_: Admin):
    return FileResponse(ROOT / "static" / "admin.html")


@app.get("/api/admin/displays")
def list_displays(_: Admin):
    with db() as conn:
        rows = conn.execute("""
            SELECT d.id, d.name, d.created_at, COUNT(p.id) AS item_count
            FROM displays d LEFT JOIN playlist_items p ON p.display_id=d.id
            GROUP BY d.id ORDER BY d.created_at
        """).fetchall()
    return [row_dict(r) for r in rows]


@app.post("/api/admin/displays", status_code=201)
def create_display(payload: DisplayCreate, _: Admin):
    with db() as conn:
        try:
            conn.execute(
                "INSERT INTO displays(id,name,created_at) VALUES(?,?,?)",
                (payload.id, payload.name.strip(), now()),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "A display with that ID already exists")
    with db() as conn:
        conn.execute("INSERT OR IGNORE INTO display_controls(display_id, mode, updated_at) VALUES (?, 'play', ?)", (payload.id, now()))
    return {"id": payload.id, "name": payload.name.strip(), "player_url": f"/display/{payload.id}"}


@app.delete("/api/admin/displays/{display_id}", status_code=204)
def delete_display(display_id: str, _: Admin):
    if display_id == "main":
        raise HTTPException(400, "The main display cannot be deleted")
    with db() as conn:
        result = conn.execute("DELETE FROM displays WHERE id=?", (display_id,))
        if result.rowcount == 0:
            raise HTTPException(404, "Display not found")
    return None


@app.get("/api/admin/media")
def list_media(_: Admin):
    with db() as conn:
        rows = conn.execute("SELECT * FROM media ORDER BY created_at DESC").fetchall()
    return [{**row_dict(r), "url": f"/media/{r['filename']}"} for r in rows]


@app.post("/api/admin/upload", status_code=201)
async def upload_media(
    _: Admin,
    file: Annotated[UploadFile, File(...)],
    display_id: Annotated[str, Form()] = "main",
    duration: Annotated[int, Form(ge=3, le=600)] = 10,
):
    original_name = Path(file.filename or "upload").name
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_IMAGE | ALLOWED_VIDEO | ALLOWED_PRESENTATION:
        raise HTTPException(415, "Supported files: JPG, PNG, WEBP, GIF, MP4, WEBM, MOV, M4V, PPT, PPTX")
    with db() as conn:
        if not conn.execute("SELECT 1 FROM displays WHERE id=?", (display_id,)).fetchone():
            raise HTTPException(404, "Display not found")

    upload_id = uuid.uuid4().hex
    if ext in ALLOWED_PRESENTATION:
        if not shutil.which("soffice") or not shutil.which("pdftoppm"):
            raise HTTPException(501, "PowerPoint conversion needs LibreOffice (soffice) and Poppler (pdftoppm). Install them and restart.")
        with tempfile.TemporaryDirectory(prefix="kids-signage-") as temp_name:
            temp = Path(temp_name)
            source = temp / f"presentation{ext}"
            await save_upload(file, source)
            try:
                proc = subprocess.run(
                    ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(temp), str(source)],
                    capture_output=True, text=True, timeout=120, check=False,
                )
                pdf = temp / "presentation.pdf"
                if proc.returncode != 0 or not pdf.exists():
                    raise HTTPException(422, "Could not convert this presentation. Check that it opens in LibreOffice.")
                render = subprocess.run(
                    ["pdftoppm", "-png", "-r", "110", str(pdf), str(temp / "slide")],
                    capture_output=True, text=True, timeout=180, check=False,
                )
                slides = sorted(temp.glob("slide-*.png"), key=lambda p: int(re.search(r"-(\d+)\.png$", p.name).group(1)))
                if render.returncode != 0 or not slides:
                    raise HTTPException(422, "Presentation converted but slide rendering failed.")
                created = []
                for index, slide in enumerate(slides, start=1):
                    filename = f"{upload_id}-slide-{index}.png"
                    shutil.copyfile(slide, safe_media_path(filename))
                    media_id = create_media_record(
                        f"{Path(original_name).stem} — Slide {index}", filename, "image", "image/png"
                    )
                    add_to_playlist(display_id, media_id, duration)
                    created.append({"id": media_id, "title": f"{Path(original_name).stem} — Slide {index}"})
                return {"uploaded": len(created), "items": created, "message": "Presentation converted to static slides."}
            except subprocess.TimeoutExpired:
                raise HTTPException(408, "Presentation conversion timed out.")
    else:
        filename = f"{upload_id}{ext}"
        target = safe_media_path(filename)
        await save_upload(file, target)
        media_type = "image" if ext in ALLOWED_IMAGE else "video"
        mime_type = mimetypes.guess_type(original_name)[0] or "application/octet-stream"
        media_id = create_media_record(Path(original_name).stem[:200], filename, media_type, mime_type)
        add_to_playlist(display_id, media_id, duration)
        return {"uploaded": 1, "items": [{"id": media_id, "title": Path(original_name).stem}], "message": "Media uploaded."}


def extract_youtube_id(raw_url: str) -> str:
    parsed = urlparse(raw_url.strip())
    host = (parsed.hostname or "").lower()
    video_id = ""
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith(("/embed/", "/shorts/", "/live/")):
            video_id = parsed.path.strip("/").split("/")[1]
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise HTTPException(400, "Enter a valid YouTube video URL.")
    return video_id


@app.post("/api/admin/youtube", status_code=201)
def add_youtube_video(
    _: Admin,
    url: Annotated[str, Form()],
    display_id: Annotated[str, Form()] = "main",
):
    video_id = extract_youtube_id(url)
    with db() as conn:
        if not conn.execute("SELECT 1 FROM displays WHERE id=?", (display_id,)).fetchone():
            raise HTTPException(404, "Display not found")
    media_id = create_media_record(
        f"YouTube video · {video_id}", video_id, "video", "video/youtube"
    )
    add_to_playlist(display_id, media_id, 60)
    return {"uploaded": 1, "items": [{"id": media_id, "title": f"YouTube video · {video_id}"}],
            "message": "YouTube video added to the selected display."}


@app.delete("/api/admin/media/{media_id}", status_code=204)
def delete_media(media_id: str, _: Admin):
    with db() as conn:
        row = conn.execute("SELECT filename FROM media WHERE id=?", (media_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Media not found")
        conn.execute("DELETE FROM media WHERE id=?", (media_id,))
    safe_media_path(row["filename"]).unlink(missing_ok=True)
    return None


@app.get("/api/admin/playlists/{display_id}")
def get_playlist(display_id: str, _: Admin):
    with db() as conn:
        if not conn.execute("SELECT 1 FROM displays WHERE id=?", (display_id,)).fetchone():
            raise HTTPException(404, "Display not found")
        rows = conn.execute("""
            SELECT m.id, m.title, m.filename, m.media_type, m.mime_type, p.position, p.duration
            FROM playlist_items p JOIN media m ON m.id=p.media_id
            WHERE p.display_id=? ORDER BY p.position, p.id
        """, (display_id,)).fetchall()
    return [{**row_dict(r), "url": f"/media/{r['filename']}"} for r in rows]


@app.put("/api/admin/playlists/{display_id}")
def update_playlist(display_id: str, payload: PlaylistUpdate, _: Admin):
    if len(payload.media_ids) != len(set(payload.media_ids)):
        raise HTTPException(400, "Duplicate media IDs are not allowed")
    with db() as conn:
        if not conn.execute("SELECT 1 FROM displays WHERE id=?", (display_id,)).fetchone():
            raise HTTPException(404, "Display not found")
        for media_id in payload.media_ids:
            if not conn.execute("SELECT 1 FROM media WHERE id=?", (media_id,)).fetchone():
                raise HTTPException(400, f"Unknown media ID: {media_id}")
        conn.execute("DELETE FROM playlist_items WHERE display_id=?", (display_id,))
        conn.executemany(
            "INSERT INTO playlist_items(display_id,media_id,position,duration) VALUES(?,?,?,?)",
            [(display_id, mid, index, payload.duration) for index, mid in enumerate(payload.media_ids)],
        )
    return {"display_id": display_id, "count": len(payload.media_ids)}


@app.get("/api/admin/displays/{display_id}/control")
def get_display_control(display_id: str, _: Admin):
    with db() as conn:
        if not conn.execute("SELECT 1 FROM displays WHERE id=?", (display_id,)).fetchone():
            raise HTTPException(404, "Display not found")
        conn.execute("INSERT OR IGNORE INTO display_controls(display_id, mode, updated_at) VALUES (?, 'play', ?)", (display_id, now()))
        row = conn.execute("SELECT mode FROM display_controls WHERE display_id=?", (display_id,)).fetchone()
    return {"display_id": display_id, "mode": row["mode"]}


@app.post("/api/admin/displays/{display_id}/control")
def set_display_control(display_id: str, payload: dict, _: Admin):
    mode = payload.get("mode")
    if mode not in {"play", "freeze", "break"}:
        raise HTTPException(400, "Mode must be play, freeze, or break")
    with db() as conn:
        if not conn.execute("SELECT 1 FROM displays WHERE id=?", (display_id,)).fetchone():
            raise HTTPException(404, "Display not found")
        conn.execute(
            "INSERT INTO display_controls(display_id, mode, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(display_id) DO UPDATE SET mode=excluded.mode, updated_at=excluded.updated_at",
            (display_id, mode, now()),
        )
    return {"display_id": display_id, "mode": mode}


@app.get("/api/player/{display_id}")
def player_playlist(display_id: str):
    with db() as conn:
        display = conn.execute("SELECT id,name FROM displays WHERE id=?", (display_id,)).fetchone()
        if not display:
            raise HTTPException(404, "Display not found")
        rows = conn.execute("""
            SELECT m.id, m.title, m.filename, m.media_type, m.mime_type, p.position, p.duration
            FROM playlist_items p JOIN media m ON m.id=p.media_id
            WHERE p.display_id=? ORDER BY p.position, p.id
        """, (display_id,)).fetchall()
        conn.execute("INSERT OR IGNORE INTO display_controls(display_id, mode, updated_at) VALUES (?, 'play', ?)", (display_id, now()))
        control = conn.execute("SELECT mode FROM display_controls WHERE display_id=?", (display_id,)).fetchone()
    return {"display": row_dict(display), "mode": control["mode"], "items": [{**row_dict(r), "url": f"/media/{r['filename']}"} for r in rows]}


@app.get("/display/{display_id}", response_class=HTMLResponse)
def player_page(display_id: str):
    with db() as conn:
        if not conn.execute("SELECT 1 FROM displays WHERE id=?", (display_id,)).fetchone():
            raise HTTPException(404, "Display not found")
    return FileResponse(ROOT / "static" / "player.html")


@app.get("/media/{filename}")
def serve_media(filename: str):
    path = safe_media_path(filename)
    if not path.is_file():
        raise HTTPException(404, "Media not found")
    return FileResponse(path)
