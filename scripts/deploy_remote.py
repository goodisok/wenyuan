"""Remote deploy via SFTP (no git clone). Usage: python deploy_remote.py HOST PASSWORD"""
from __future__ import annotations

import os
import pathlib
import sys
import textwrap

import paramiko

from nginx_config import DOMAIN, nginx_config

HOST = sys.argv[1] if len(sys.argv) > 1 else "119.91.54.153"
USER = "ubuntu"
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else ""
ROOT = pathlib.Path(__file__).resolve().parents[1]
REMOTE = "/opt/wenyuan"
SKIP_DIRS = {".git", "venv", "__pycache__", ".pytest_cache", "node_modules", "scripts", ".cursor"}
SKIP_FILES = {".env"}
SKIP_PREFIXES = ("_tmp_", "_prod_")


def should_skip(path: pathlib.Path) -> bool:
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    if path.name in SKIP_FILES and path.parent == ROOT:
        return True
    if any(path.name.startswith(p) for p in SKIP_PREFIXES):
        return True
    return False


def upload_tree(sftp: paramiko.SFTPClient, local: pathlib.Path, remote: str) -> None:
    for item in local.iterdir():
        if should_skip(item):
            continue
        rpath = f"{remote}/{item.name}"
        if item.is_dir():
            try:
                sftp.mkdir(rpath)
            except OSError:
                pass
            upload_tree(sftp, item, rpath)
        else:
            print("upload", item.relative_to(ROOT))
            sftp.put(str(item), rpath)


def main() -> None:
    if not PASSWORD:
        print("Usage: python deploy_remote.py HOST PASSWORD", file=sys.stderr)
        sys.exit(1)

    env_text = (ROOT / ".env").read_text(encoding="utf-8")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=60, banner_timeout=60)

    def run(cmd: str, timeout: int = 600) -> str:
        print(">>>", cmd[:120])
        _stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        channel = stdout.channel
        channel.settimeout(timeout)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = channel.recv_exit_status()
        if out.strip():
            tail = out[-4000:] if len(out) > 4000 else out
            print(tail)
        if code != 0:
            print(err[-4000:])
            raise SystemExit(f"Command failed ({code})")
        return out

    run("sudo mkdir -p /opt/wenyuan && sudo chown -R ubuntu:ubuntu /opt/wenyuan")
    run("sudo mkdir -p /var/www/certbot")

    cert_check = run(
        f"sudo test -f /etc/letsencrypt/live/{DOMAIN}/fullchain.pem && echo yes || echo no"
    ).strip()
    use_ssl = cert_check.endswith("yes")

    sftp = client.open_sftp()
    upload_tree(sftp, ROOT, REMOTE)
    with sftp.file(f"{REMOTE}/.env", "w") as remote_env:
        remote_env.write(env_text)
    sftp.chmod(f"{REMOTE}/.env", 0o600)
    sftp.close()

    run(
        f"cd {REMOTE} && python3 -m venv venv && "
        "./venv/bin/pip install -U pip -q && "
        "./venv/bin/pip install -r requirements.txt -q",
        timeout=900,
    )

    service = textwrap.dedent(
        """
        [Unit]
        Description=Wenyuan FastAPI
        After=network.target

        [Service]
        Type=simple
        User=ubuntu
        WorkingDirectory=/opt/wenyuan
        EnvironmentFile=/opt/wenyuan/.env
        ExecStart=/opt/wenyuan/venv/bin/python run.py
        Restart=always
        RestartSec=3

        [Install]
        WantedBy=multi-user.target
        """
    ).strip()

    nginx = nginx_config(ssl=use_ssl, host=HOST)

    run(f"cat > /tmp/wenyuan.service <<'EOF'\n{service}\nEOF")
    run("sudo mv /tmp/wenyuan.service /etc/systemd/system/wenyuan.service")
    run(f"cat > /tmp/wenyuan.nginx <<'EOF'\n{nginx}\nEOF")
    run("sudo mv /tmp/wenyuan.nginx /etc/nginx/sites-available/wenyuan")
    run("sudo ln -sf /etc/nginx/sites-available/wenyuan /etc/nginx/sites-enabled/wenyuan")
    run("sudo rm -f /etc/nginx/sites-enabled/default")
    run("sudo nginx -t")
    run("sudo systemctl daemon-reload")
    run("sudo systemctl enable wenyuan")
    run("sudo systemctl restart wenyuan")
    run("sudo systemctl restart nginx")
    run("sleep 2 && curl -sS http://127.0.0.1:8000/health")
    print(run("curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1/"))
    client.close()
    scheme = "https" if use_ssl else "http"
    print(f"Deployed: {scheme}://{DOMAIN}/ (IP: http://{HOST}/)")


if __name__ == "__main__":
    main()
