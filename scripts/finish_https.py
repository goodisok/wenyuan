"""Re-apply SSL nginx when Let's Encrypt cert already exists."""
from __future__ import annotations

import paramiko
from nginx_config import DOMAIN, nginx_config

HOST = "119.91.54.153"
USER = "ubuntu"
PASSWORD = "Goodisok123"


def main() -> None:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=60)

    def run(cmd: str, timeout: int = 600) -> str:
        print(">>>", cmd[:120])
        _stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        if out.strip():
            print(out[-3000:])
        if code != 0:
            print(err[-3000:])
            raise SystemExit(code)
        return out

    run(
        "sudo test -f /etc/letsencrypt/options-ssl-nginx.conf || "
        "sudo curl -fsSL "
        "https://raw.githubusercontent.com/certbot/certbot/v1.21.0/"
        "certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf "
        "-o /etc/letsencrypt/options-ssl-nginx.conf"
    )
    conf = nginx_config(ssl=True, host=HOST)
    run(f"cat > /tmp/wenyuan.nginx <<'EOF'\n{conf}\nEOF")
    run("sudo mv /tmp/wenyuan.nginx /etc/nginx/sites-available/wenyuan")
    run("sudo nginx -t")
    run("sudo systemctl reload nginx")
    run(f"curl -sS --resolve {DOMAIN}:443:127.0.0.1 https://{DOMAIN}/health")
    client.close()


if __name__ == "__main__":
    main()
