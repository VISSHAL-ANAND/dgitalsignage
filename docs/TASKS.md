# Tasks

## P0 — Before lab demonstration
- [ ] Clone repository on the Raspberry Pi 5 and install using scripts/install_pi.sh.
- [ ] Confirm the generated admin password and sign in at /admin.
- [ ] Upload a representative image and MP4; verify playback on the attached display.
- [ ] Upload a representative PPTX; verify LibreOffice conversion and slide order.
- [ ] Add a second display in the dashboard and test its independent player URL.
- [ ] Reboot the Pi and confirm systemd restarts the service.
- [ ] Test temporary network loss and ensure the player reconnects to the local server.
- [ ] Confirm admin access is restricted to the intended network/VPN; do not expose port 8080 publicly.

## P1 — Engineering hardening
- [x] Add initial automated API tests for authentication, uploads, display creation, playlist isolation, and media serving (deletion coverage remains to add).
- [ ] Add browser-based end-to-end tests.
- [ ] Add upload content-signature validation and optional malware scanning.
- [ ] Add file count/storage quotas and cleanup/backup instructions.
- [ ] Add explicit player error states and recoverable video playback handling.
- [ ] Verify and document supported codecs/resolutions on Raspberry Pi 5.
- [ ] Evaluate Anthias integration after comparing its playback and management behavior with this MVP.

## P2 — Product improvements
- [ ] User accounts/roles and approval workflow.
- [ ] Scheduling by start/end date and time.
- [ ] Playlist preview and drag-and-drop reordering.
- [ ] Display heartbeat/health monitoring.
- [ ] Remote access guide using university-approved VPN or private overlay network.
