# KIDS LAB Digital Signage

**Self-hosted digital signage for Karunya University’s KIDS LAB**  
Designed for Raspberry Pi 5, with a browser-based administration dashboard and fullscreen playback for one or more displays.

> ### One place to manage lab content. A reliable fullscreen player on every display.
>
> Upload images, videos, and PowerPoint presentations, organize content for each screen, and run the player locally on the lab network.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](requirements.txt)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)](app.py)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%205-red)](https://www.raspberrypi.com/products/raspberry-pi-5/)
[![License](https://img.shields.io/badge/License-See%20repository-lightgrey)](LICENSE)

---

## Contents

- [Overview](#1-overview)
- [Features](#2-features)
- [How it works](#3-how-it-works)
- [Requirements](#4-requirements)
- [Quick start: local development](#5-quick-start-local-development)
- [Raspberry Pi 5 deployment](#6-raspberry-pi-5-deployment)
- [Accessing the dashboard and displays](#7-accessing-the-dashboard-and-displays)
- [Media and PowerPoint support](#8-media-and-powerpoint-support)
- [Configuration](#9-configuration)
- [Project structure](#10-project-structure)
- [Operations and maintenance](#11-operations-and-maintenance)
- [Security and remote access](#12-security-and-remote-access)
- [Troubleshooting](#13-troubleshooting)
- [Testing and deployment checklist](#14-testing-and-deployment-checklist)
- [Roadmap](#15-roadmap)
- [Contributing](#16-contributing)

---

## 1. Overview

KIDS LAB Digital Signage is a self-hosted application for publishing announcements, educational material, images, videos, and presentation slides to displays in a lab or shared space.

The application runs as a web service on a local computer or Raspberry Pi. Administrators manage content from a browser, while each display opens a dedicated player URL. This keeps content management separate from the screen that presents it.

### Design goals

- **Simple administration:** Manage content through a browser rather than editing files by hand.
- **Local-first operation:** Host the application on the lab network without requiring a cloud service for normal playback.
- **Multiple displays:** Give each screen its own display URL and content assignment.
- **Raspberry Pi deployment:** Support a compact, low-power player intended for continuous operation.
- **Clear operational behavior:** Make service health, setup requirements, and optional conversion dependencies explicit.

This repository is an evolving project. Check the actual deployment and test results before treating any feature as production-validated.

## 2. Features

### Content management

- Upload supported image and video files.
- Upload PowerPoint `.ppt` and `.pptx` presentations when the required conversion tools are installed.
- Keep media files and application metadata on the host.
- Use the browser-based administration interface to manage the signage content.

### Display playback

- Open a fullscreen player at `/display/<display_id>`.
- Use a separate display identifier for each configured screen.
- Run the player in a Chromium kiosk session on a Raspberry Pi desktop.
- Configure the Raspberry Pi to start the signage player automatically after graphical login.

### Application and storage

- FastAPI web application.
- SQLite metadata database.
- Local media storage.
- HTTP Basic authentication for administration.
- Optional PowerPoint conversion through LibreOffice and Poppler utilities.

> **Important:** Exact behavior depends on the code version deployed. Validate each media type and display workflow on the target hardware before unattended use.

## 3. How it works

```text
Administrator's laptop / browser
              |
              | Local network (HTTP)
              v
     KIDS LAB web application
       FastAPI + SQLite
              |
       +------+------+
       |             |
       v             v
  Media storage   Display configuration
                     |
           +---------+---------+
           |                   |
           v                   v
      Display 1             Display 2
    /display/main       /display/<id>
           |                   |
           v                   v
     Fullscreen player   Fullscreen player
```

Typical workflow:

1. An administrator signs in to the dashboard.
2. The administrator uploads media or a presentation.
3. The application stores media and its associated metadata.
4. Content is assigned to a display or playlist using the available dashboard features.
5. The display browser opens its dedicated player route and presents the assigned content.

The administration interface and display player are separate routes. Display pages are designed to be accessible without administrator credentials so that a screen can play content without an interactive login.

## 4. Requirements

### Hardware

For the intended Raspberry Pi installation:

- Raspberry Pi 5.
- Compatible power supply.
- microSD card or other supported boot storage.
- HDMI-compatible display and cable.
- Network connection for administration and updates.
- Optional keyboard and mouse for local troubleshooting; headless administration can be performed over SSH once networking is configured.

### Software

- Raspberry Pi OS 64-bit or another compatible Linux environment.
- Python 3.11 or newer for the application environment.
- Git.
- Python dependencies listed in `requirements.txt`.
- Chromium and a working graphical desktop session for HDMI kiosk playback.
- LibreOffice (`soffice`) and Poppler (`pdftoppm`) for PowerPoint conversion; these are optional for basic image/video use.

## 5. Quick start: local development

### 5.1 Clone the repository

```bash
git clone https://github.com/VISSHAL-ANAND/dgitalsignage.git
cd dgitalsignage
```

### 5.2 Create and activate a virtual environment

**Linux / macOS (Bash or Zsh):**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Fish shell:**

```fish
python3 -m venv .venv
source .venv/bin/activate.fish
```

**Windows PowerShell:**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 5.3 Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If your operating system manages system Python packages, use the virtual environment rather than installing packages into system Python.

### 5.4 Configure the application

Create a local environment file:

```bash
cp .env.example .env
```

Open `.env` and configure the administrator credentials and other settings supported by the current application. Use a strong, unique password. Do not commit `.env` or secrets to Git.

If `.env.example` is missing or configuration names have changed, inspect `app.py` and the current repository documentation instead of guessing environment variable names.

### 5.5 Start the application

From the repository root, with the virtual environment active:

```bash
uvicorn app:app --host 0.0.0.0 --port 8080
```

For laptop-only testing, bind to `127.0.0.1` instead of `0.0.0.0` if you do not need other devices to connect.

Open the dashboard at:

```text
http://127.0.0.1:8080/admin
```

Open the main display route at:

```text
http://127.0.0.1:8080/display/main
```

Stop the development server with `Ctrl+C`.

## 6. Raspberry Pi 5 deployment

The Pi deployment uses a system service so the web application can run independently of an SSH session. The kiosk browser is a separate graphical-session responsibility.

### 6.1 Prepare Raspberry Pi OS

1. Install Raspberry Pi OS 64-bit.
2. Configure a hostname, user account, and network access.
3. Enable SSH if managing the Pi headlessly.
4. Boot the Pi and connect from the laptop:

```bash
ssh <pi-user>@<pi-hostname-or-ip>
```

Replace the placeholders with the actual username and address for your device.

### 6.2 Install the application

From the Pi's SSH session, clone the repository and follow the deployment script shipped with the current version:

```bash
git clone https://github.com/VISSHAL-ANAND/dgitalsignage.git
cd dgitalsignage
```

If the repository contains `scripts/install_pi.sh`, inspect it before running it and then execute it according to its documented requirements:

```bash
less scripts/install_pi.sh
```

The installer may require `sudo` to install system packages or configure the service. Read the script and its output carefully; do not run an installer from an untrusted source as root.

### 6.3 Verify the service

For the current systemd deployment, check the service state:

```bash
sudo systemctl status kids-signage.service
```

Check the application health endpoint:

```bash
curl -fsS http://127.0.0.1:8080/health
```

A healthy deployment is expected to return a JSON response indicating that the service is healthy. If this request fails, inspect the service logs:

```bash
sudo journalctl -u kids-signage.service -n 100 --no-pager
```

### 6.4 Open the dashboard from the laptop

Find the Pi's current LAN IP address or use its configured hostname. Then open:

```text
http://<pi-ip-address>:8080/admin
```

The display player can be opened at:

```text
http://<pi-ip-address>:8080/display/main
```

Use the administrator credentials configured during installation. Do not store passwords in this README.

### 6.5 Configure HDMI kiosk playback

The kiosk browser must start inside the graphical desktop session used by the connected display. A running web service alone does not guarantee that anything appears on HDMI.

For a Labwc session, a user-level autostart file can wait for the local health endpoint and then launch Chromium:

```sh
#!/bin/sh
(
  until curl -fsS http://127.0.0.1:8080/health >/dev/null; do
    sleep 2
  done
  sleep 3
  chromium --kiosk --no-first-run --disable-infobars --noerrdialogs \
    http://127.0.0.1:8080/display/main
) &
```

Place this script in the Labwc autostart location for the user and desktop session actually in use (commonly `~/.config/labwc/autostart`), and make it executable. Confirm that LightDM automatic login and the intended Labwc session are configured before rebooting. Desktop/session details can vary by Raspberry Pi OS release.

Test in this order:

1. Open the display URL manually in Chromium.
2. Confirm that the correct content fills the HDMI screen.
3. Confirm the autostart script runs in the active graphical session.
4. Reboot and verify recovery.
5. Test again after temporarily interrupting network access.

Do not assume the kiosk is configured successfully until the actual HDMI screen has been checked.

## 7. Accessing the dashboard and displays

| Purpose | Route | Use |
|---|---|---|
| Administration | `/admin` | Sign in and manage signage |
| Main display | `/display/main` | Player for the main screen |
| Other displays | `/display/<display_id>` | Player for a configured display |
| Health check | `/health` | Check whether the application responds |

For a local application, substitute `127.0.0.1` for the host. For a Raspberry Pi, use the Pi's LAN IP or hostname.

Example:

```text
http://192.168.1.50:8080/admin
http://192.168.1.50:8080/display/main
http://192.168.1.50:8080/health
```

The IP address above is only an example; use the address assigned to your device. The main display identifier shown here is `main`; use identifiers that actually exist in your installation for other displays.

## 8. Media and PowerPoint support

### Images and videos

Upload representative files and verify playback on the actual display. Browser codec support, resolution, bitrate, and file size can affect playback. Use a consistent aspect ratio where possible and test large files before deploying them to every screen.

### PowerPoint presentations

PowerPoint files are converted to static slide images when the required tools are available:

- **LibreOffice:** provides the `soffice` command used to render presentations.
- **Poppler:** provides `pdftoppm`, used to convert PDF pages to images.

Install these through the operating system's trusted package manager. For Debian/Raspberry Pi OS, the package names are commonly `libreoffice` and `poppler-utils`.

Verify the commands are available:

```bash
command -v soffice
command -v pdftoppm
```

Conversion to static images does not preserve every presentation feature. Animations, transitions, embedded video/audio, interactive content, and some fonts may not render as expected. Test important presentations before relying on them for an event or unattended display.

## 9. Configuration

The repository includes `.env.example` as the starting point for local configuration. The current deployment may use a separate environment file managed by systemd.

Common configuration concepts include:

| Setting | Purpose |
|---|---|
| Administrator username/password | Protect the management interface |
| Data directory | Store the database and uploaded media |
| Upload size limit | Bound the size of incoming media files |
| Host and port | Control which interface and port serve the application |

**Use the actual names and defaults defined in `.env.example` and the application code.** Do not copy guessed variable names from an older README or expose secret values in issue reports.

For the deployed Raspberry Pi service, inspect service configuration without sharing secrets:

```bash
sudo systemctl cat kids-signage.service
```

If environment values are stored in a protected file such as `/etc/kids-signage.env`, do not paste that file's contents into chat, issues, screenshots, or public logs.

## 10. Project structure

The exact tree can evolve. The main files and locations used by the current project include:

```text
dgitalsignage/
├── app.py                  # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env.example            # Example local configuration
├── scripts/
│   └── install_pi.sh       # Raspberry Pi installation helper, if present
├── data/                   # Local development data (runtime)
└── README.md               # Project documentation
```

On the installed Raspberry Pi deployment, the service and data may live outside the cloned repository. The current deployment described for the lab uses:

- Application: `/opt/kids-signage`
- Persistent data: `/var/lib/kids-signage`
- Service environment file: `/etc/kids-signage.env`
- systemd unit: `kids-signage.service`

Treat these as deployment paths, not as paths guaranteed to exist in every local development environment. The system service should run the installed copy of the application, while the Git checkout is used for source management and updates.

## 11. Operations and maintenance

### Check service status

```bash
sudo systemctl status kids-signage.service
```

### View recent logs

```bash
sudo journalctl -u kids-signage.service -n 100 --no-pager
```

Follow logs live:

```bash
sudo journalctl -u kids-signage.service -f
```

### Restart the application

```bash
sudo systemctl restart kids-signage.service
```

### Confirm the health endpoint

```bash
curl -fsS http://127.0.0.1:8080/health
```

### Back up persistent data

Back up the actual configured data directory, including the SQLite database and uploaded media. Before copying a live SQLite database, use an application-aware backup or stop the service briefly to avoid an inconsistent copy. Store backups somewhere separate from the Pi's SD card and periodically verify that they can be restored.

### Updates

Before updating a live display:

1. Back up the database and media.
2. Review repository changes and installation instructions.
3. Update a test installation first when possible.
4. Apply the update during a maintenance window.
5. Check the systemd service, health endpoint, dashboard, and display playback.
6. Keep a known-good revision and backup for recovery.

Do not delete the persistent data directory as a routine update step.

## 12. Security and remote access

The application is intended for a trusted lab network unless additional protections are configured.

- **Do not expose port 8080 directly to the public internet.**
- Use a strong, unique administrator password and rotate any credential that has been shared or exposed.
- Do not commit `.env`, private configuration files, tokens, passwords, or uploaded private media.
- HTTP Basic authentication over plain HTTP does not encrypt credentials. Use a university-approved VPN/private network, or a properly configured HTTPS reverse proxy for remote administration.
- Restrict network access to the administration interface where practical.
- Keep Raspberry Pi OS and Python dependencies updated.
- Review who can access display URLs: they are designed for playback without administrator authentication.
- Do not upload confidential or personal information until storage, display access, and network controls have been reviewed.
- Treat uploaded files as untrusted input and keep the host and conversion tools patched.

For university use, follow Karunya University's network and information-security policies before enabling remote access.

## 13. Troubleshooting

### The dashboard does not open

1. Confirm that the Pi and laptop are on a network that permits communication.
2. Check the Pi's current IP address.
3. Run `sudo systemctl status kids-signage.service` on the Pi.
4. Run `curl -fsS http://127.0.0.1:8080/health` on the Pi.
5. Inspect logs with `sudo journalctl -u kids-signage.service -n 100 --no-pager`.
6. Check whether a firewall or network policy blocks port 8080.

### The display is blank, white, or stuck

- Open `/display/main` in a normal browser on the laptop to distinguish application problems from kiosk/HDMI problems.
- Check service health and logs.
- Confirm that the correct display identifier exists.
- Verify the HDMI input, cable, and display resolution.
- Confirm that a graphical desktop session is running on the Pi.
- Check the Labwc autostart file and Chromium process in the graphical session.
- Review Chromium/session errors before changing desktop packages or display-manager settings.

A healthy API does not by itself prove that Chromium or HDMI playback is working.

### Chromium does not start automatically

- Confirm LightDM is active and configured for the intended user.
- Confirm the session selected by LightDM is the expected Labwc session.
- Check that the autostart file is in the correct user's home directory and is executable.
- Confirm `curl` and `chromium` are installed.
- Launch Chromium manually from the graphical session to see errors.
- Inspect system and user logs before changing autologin or desktop configuration.

### PowerPoint upload or conversion fails

- Verify `soffice` and `pdftoppm` with `command -v`.
- Check available disk space and upload size limits.
- Try a simple presentation to determine whether the problem is file-specific.
- Review application logs for the actual conversion error.

### Admin authentication fails

- Use the credentials configured for the running service, not an old local `.env` file.
- Do not share the protected environment file or password in a support request.
- Follow the project's credential-reset procedure and restart the service if the configuration requires it.

## 14. Testing and deployment checklist

Before using the system for unattended lab signage, verify each item on the actual hardware.

### Application

- [ ] Dependencies install successfully in a virtual environment.
- [ ] Application starts and the health endpoint responds.
- [ ] Admin login works with a unique password.
- [ ] Supported image uploads succeed.
- [ ] Supported video uploads and playback succeed.
- [ ] PowerPoint conversion works when optional dependencies are installed.
- [ ] Missing conversion dependencies produce a clear error.
- [ ] Database and uploaded media survive a service restart.

### Displays

- [ ] Main display URL opens and fills the screen.
- [ ] Each additional configured display uses the intended content.
- [ ] Media renders correctly at the target resolution.
- [ ] Chromium kiosk mode starts in the graphical session.
- [ ] Reboot starts the service and display player without manual intervention.
- [ ] Playback recovers after a temporary network interruption where applicable.
- [ ] Long-running playback is tested for stability.

### Operations and security

- [ ] Persistent data is backed up.
- [ ] Service logs are accessible.
- [ ] Administrator credentials are unique and protected.
- [ ] Port 8080 is not publicly exposed without appropriate protections.
- [ ] The university network policy has been reviewed.
- [ ] Recovery from a failed update or damaged SD card has been considered.

Do not mark a checklist item complete until it has been tested.

## 15. Roadmap

Potential next improvements, subject to implementation and testing:

- More robust playlist scheduling and content ordering.
- Better per-display status and troubleshooting.
- Safer upload validation and clearer media-processing feedback.
- Automated backup and restore guidance.
- More complete deployment and update automation.
- Evaluation of [Anthias](https://github.com/Screenly/Anthias) as an optional integration or alternative player, only after testing it on the target Raspberry Pi hardware.

Items in this roadmap are proposals, not claims that the features are already implemented.

## 16. Contributing

Contributions and bug reports are welcome.

When reporting an issue, include:

- Raspberry Pi / operating system details, if relevant.
- Python version.
- The action that triggered the problem.
- Relevant error messages with secrets and personal data removed.
- Whether the problem occurs locally, on the Pi service, or only in the HDMI kiosk session.
- Reproduction steps.

Do not include passwords, environment-file contents, private media, or sensitive network details in public issues.

Before submitting a change, test the affected workflow and update the documentation if setup, configuration, or operational behavior changes.

---

## Project links

- **Repository:** https://github.com/VISSHAL-ANAND/dgitalsignage
- **Reference project style:** https://github.com/VISSHAL-ANAND/hacknex.R1

**KIDS LAB Digital Signage — dependable content management for lab displays, built to run on hardware you control.**
