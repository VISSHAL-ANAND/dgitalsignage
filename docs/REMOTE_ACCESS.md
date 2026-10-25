# Local and remote access

## Local access

After installation, find the Pi's LAN address and open these URLs from a computer on the same permitted network:

- Admin: http://PI_LAN_IP:8080/admin
- Main player: http://PI_LAN_IP:8080/display/main
- Health check: http://PI_LAN_IP:8080/health

Use the password generated during installation. The password is stored in /etc/kids-signage.env and can be read on the Pi with sudo.

## Remote access recommendation

Do not port-forward TCP 8080 from the public internet. HTTP Basic authentication is not encrypted by plain HTTP.

Preferred order:
1. Use the university's approved VPN, if available.
2. Otherwise, ask the lab/IT administrator whether a private overlay VPN such as Tailscale is permitted. Install it on the Pi and the admin laptop using the vendor's official instructions, sign both devices into the same approved tailnet, and restrict access to the intended users.
3. Open the admin URL using the Pi's private VPN address. Do not enable public funneling or public port forwarding for this MVP.

The exact network approach depends on university policy and the network configuration available in the lab. This repository does not automatically configure VPN access or create a public HTTPS endpoint.

## Multiple screens

Each physical screen can open a different player URL, for example:

- http://PI_LAN_IP:8080/display/main
- http://PI_LAN_IP:8080/display/innovation-zone

Create additional display IDs from the admin dashboard. This MVP serves all screens from one signage server; each screen needs network access to that server. Independent Raspberry Pi servers and centralized fleet synchronization are not implemented yet.
