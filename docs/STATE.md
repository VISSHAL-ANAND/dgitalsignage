# Project state

Updated: 2026-10-26

## Goal
Self-hosted KIDS LAB signage manager for Raspberry Pi 5 and multiple screens, with local and secure remote administration.

## Implemented in repository
- FastAPI application with SQLite metadata storage.
- HTTP Basic authentication for admin routes (requires ADMIN_PASSWORD).
- Upload support for images and videos.
- Optional PPT/PPTX conversion to static slide images using LibreOffice and Poppler.
- Multiple display records, per-display playlists, playlist ordering, and public fullscreen player routes.
- Admin dashboard, responsive styling, health endpoint, systemd service template, and Raspberry Pi installation helper.

## Known limitations / not yet verified
- Automated API tests now cover health, admin authentication, display creation, media upload, playlist isolation, and media serving; GitHub Actions passed on the implementation commit.
- Not tested on Raspberry Pi 5 hardware or an attached display.
- No end-to-end browser tests.
- Video codec compatibility depends on browser/OS hardware decoding.
- PowerPoint animations, transitions, and embedded media are not preserved by static rendering.
- The admin UI uses browser HTTP Basic authentication. Use only on a trusted local network or behind an approved VPN/TLS layer; do not expose raw HTTP to the internet.
- Multi-display support currently means multiple display URLs/playlists served by this application. It is not a distributed multi-server CMS.
- Anthias has not yet been integrated; it remains an option to validate against the direct browser-player MVP.

## Immediate deployment caution
Before connecting this to a university network, confirm network policy, set a strong password, check storage capacity, and validate file upload and playback behavior.
