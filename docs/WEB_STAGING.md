# Web staging deployment

This branch adds a Docker build for temporary browser-based acceptance testing. It does not replace the Raspberry Pi deployment.

## Recommended hosting settings

Use a staging service connected to branch `staging/web-test` in `VISSHAL-ANAND/dgitalsignage`.

1. Build with the repository `Dockerfile`.
2. Set a strong, unique `ADMIN_PASSWORD` environment variable. Optionally set `ADMIN_USER` (defaults to `admin`).
3. Attach a persistent volume at `/data`. The app stores its SQLite database and uploaded media in `DATA_DIR`, set to `/data` in the container.
4. Expose the service over HTTPS using the host's generated domain. The container listens on the platform-provided `PORT`.
5. Keep this deployment for test content only. The player routes are intentionally public and anyone with a display URL may view that display's playlist. Do not upload confidential or student-identifying content.
6. Restrict admin access if the hosting platform supports access controls. Do not share the admin password in chat, code, or repository files.

The container includes LibreOffice Impress and Poppler utilities for PowerPoint-to-slide-image conversion. Rendering may differ from the Raspberry Pi due to fonts, codecs, and browser behavior.

## Smoke-test checklist

- `/health` returns JSON with `status: ok`.
- `/admin` prompts for admin credentials and opens after valid authentication.
- Upload a JPG/PNG, an MP4, and a simple PPTX with 2–3 slides.
- Create a second display and assign different media to it.
- Open `/display/main` and `/display/<second-display-id>` in separate browser tabs and confirm playlists are isolated.
- Refresh the page and restart/redeploy the service; confirm database and uploaded files persist on the mounted volume.
- Check browser console and server logs for errors.
- Confirm the deployment is HTTPS before entering admin credentials.

## Known boundaries

A successful cloud test does not prove HDMI output, kiosk mode, Raspberry Pi hardware decoding, unattended startup, or long-run stability. These require testing on the target Pi and display. This is a staging environment; do not merge the branch into `main` until the smoke tests pass.
