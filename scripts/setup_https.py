"""Obtain Let's Encrypt cert and enable HTTPS for wenyuan.online.

Usage: python scripts/setup_https.py [HOST] [PASSWORD] [EMAIL]
"""
from __future__ import annotations

import sys

import paramiko

from nginx_config import DOMAIN, nginx_config

HOST = sys.argv[1] if len(sys.argv) > 1 else "119.91.54.153"
USER = "ubuntu"
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else ""
EMAIL = sys.argv[3] if len(sys.argv) > 3 else f"admin@{DOMAIN}"


def main() -> None:
    if not PASSWORD:
        print("Usage: python scripts/setup_https.py [HOST] [PASSWORD] [EMAIL]", file=sys.stderr)
        sys.exit(1)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=60, banner_timeout=60)

    def run(cmd: str, timeout: int = 600) -> str:
        print(">>>", cmd[:140])
        _stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        channel = stdout.channel
        channel.settimeout(timeout)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = channel.recv_exit_status()
        if out.strip():
            print(out[-6000:] if len(out) > 6000 else out)
        if code != 0:
            print(err[-6000:])
            raise SystemExit(f"Command failed ({code})")
        return out

    run("sudo apt-get update -qq")
    run("sudo apt-get install -y certbot python3-certbot-nginx")
    run("sudo mkdir -p /var/www/certbot")

    http_only = nginx_config(ssl=False, host=HOST)
    run(f"cat > /tmp/wenyuan.nginx <<'EOF'\n{http_only}\nEOF")
    run("sudo mv /tmp/wenyuan.nginx /etc/nginx/sites-available/wenyuan")
    run("sudo nginx -t")
    run("sudo systemctl reload nginx")

    run(
        "sudo certbot certonly --webroot -w /var/www/certbot "
        f"-d {DOMAIN} -d www.{DOMAIN} "
        f"--non-interactive --agree-tos --email {EMAIL} --no-eff-email",
        timeout=300,
    )
    run(
        "sudo test -f /etc/letsencrypt/ssl-dhparams.pem || "
        "sudo openssl dhparam -out /etc/letsencrypt/ssl-dhparams.pem 2048"
    )
    run(
        "sudo test -f /etc/letsencrypt/options-ssl-nginx.conf || "
        "sudo curl -fsSL "
        "https://raw.githubusercontent.com/certbot/certbot/v1.21.0/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf "
        "-o /etc/letsencrypt/options-ssl-nginx.conf"
    )

    ssl_conf = nginx_config(ssl=True, host=HOST)
    run(f"cat > /tmp/wenyuan.nginx <<'EOF'\n{ssl_conf}\nEOF")
    run("sudo mv /tmp/wenyuan.nginx /etc/nginx/sites-available/wenyuan")
    run("sudo nginx -t")
    run("sudo systemctl reload nginx")

    run(f"curl -sS https://{DOMAIN}/health")
    print(f"HTTPS ready: https://{DOMAIN}/")
    client.close()


if __name__ == "__main__":
    main()
