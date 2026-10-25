#!/usr/bin/env bash
set -euo pipefail
# Run from the cloned repository on Raspberry Pi OS 64-bit.
if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo: sudo bash scripts/install_pi.sh"
  exit 1
fi
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
apt-get update
apt-get install -y python3 python3-venv python3-pip libreoffice-writer poppler-utils
if ! id kids-signage >/dev/null 2>&1; then
  useradd --system --home /var/lib/kids-signage --shell /usr/sbin/nologin kids-signage
fi
install -d -o root -g kids-signage -m 0750 /opt/kids-signage
install -d -o kids-signage -g kids-signage -m 0750 /var/lib/kids-signage
cp -a "$REPO_DIR/." /opt/kids-signage/
chown -R root:kids-signage /opt/kids-signage
chmod -R o-rwx /opt/kids-signage
python3 -m venv /opt/kids-signage/.venv
/opt/kids-signage/.venv/bin/pip install --upgrade pip
/opt/kids-signage/.venv/bin/pip install -r /opt/kids-signage/requirements.txt
if [[ ! -f /etc/kids-signage.env ]]; then
  ADMIN_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  printf 'ADMIN_USER=admin\nADMIN_PASSWORD=%s\nDATA_DIR=/var/lib/kids-signage\nMAX_UPLOAD_MB=200\n' "$ADMIN_PASSWORD" > /etc/kids-signage.env
  chmod 0640 /etc/kids-signage.env
  chown root:kids-signage /etc/kids-signage.env
  echo "Generated admin password stored in /etc/kids-signage.env"
  echo "Retrieve it locally with: sudo cat /etc/kids-signage.env"
fi
install -m 0644 /opt/kids-signage/deploy/kids-signage.service /etc/systemd/system/kids-signage.service
systemctl daemon-reload
systemctl enable --now kids-signage
systemctl --no-pager --full status kids-signage || true
echo
echo "Service installed. Check: curl http://127.0.0.1:8080/health"
echo "Admin dashboard: http://<raspberry-pi-ip>:8080/admin"
echo "Default player:   http://<raspberry-pi-ip>:8080/display/main"
echo "Do not expose port 8080 directly to the public internet."
