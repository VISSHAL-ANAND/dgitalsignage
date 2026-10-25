# KIDS LAB Digital Signage

A self-hosted digital signage manager designed for Raspberry Pi 5 and one or more lab displays. The first milestone provides a browser-based admin dashboard, media uploads, per-display playlists, and a fullscreen player. Anthias remains an integration candidate; validate it on the target hardware before making it a dependency.

## MVP scope

- Upload images and videos.
- Upload `.ppt` / `.pptx` and convert slides to images when LibreOffice and Poppler are installed.
- Manage multiple displays and assign content to each display.
- Play playlists in a fullscreen browser at `/display/<display_id>`.
- Require HTTP Basic authentication for administration.
- Persist metadata in SQLite and media under `data/`.

## Requirements

- Python 3.11+
- `pip install -r requirements.txt`
- For PowerPoint conversion: LibreOffice (`soffice`) and Poppler (`pdftoppm`). These are optional; presentation uploads return a clear error if conversion tools are missing.

## Run locally

1. `cp .env.example .env` and set a strong `ADMIN_PASSWORD`.
2. Create a virtual environment and install requirements.
3. Run `uvicorn app:app --host 0.0.0.0 --port 8080`.
4. Open `http://<server-ip>:8080/admin` and authenticate using the configured admin credentials.
5. Open `http://<server-ip>:8080/display/main` on the screen connected to the player.

For a Raspberry Pi, use Raspberry Pi OS 64-bit and test media formats/resolution on the actual display before unattended deployment.

## Remote access and security

Do not expose port 8080 directly to the public internet. For remote administration, use a university-approved VPN or a private overlay network such as Tailscale. If using a public reverse proxy, terminate HTTPS, restrict access, use a strong unique password, and review the university's network policy first. HTTP Basic authentication is not safe over plain HTTP on an untrusted network.

The display routes are intentionally readable without admin credentials so a screen can play content without logging in. Keep the server on a trusted network and do not upload confidential material unless access controls have been reviewed.

## PowerPoint limitations

Presentations are rendered into static slide images. Complex animations, transitions, embedded media, and some fonts may not be preserved. Validate representative lab presentations before relying on this feature.

## Current status

This is an initial MVP scaffold, not yet validated on Raspberry Pi 5 hardware. Before lab deployment, test uploads, conversion, playback, reboot recovery, storage capacity, network interruption, and each display's configuration.
