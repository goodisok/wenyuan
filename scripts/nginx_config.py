"""Shared Nginx config for wenyuan deploy / HTTPS setup."""
from __future__ import annotations

import textwrap

DOMAIN = "wenyuan.online"


def _proxy_locations() -> str:
    return textwrap.dedent(
        """
            client_max_body_size 2m;
            location / {
                proxy_pass http://127.0.0.1:8000;
                proxy_http_version 1.1;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_read_timeout 300s;
                proxy_buffering off;
            }
            location /static/ {
                alias /opt/wenyuan/static/;
                expires 7d;
            }
        """
    ).strip()


def nginx_config(*, ssl: bool, host: str) -> str:
    proxy = _proxy_locations()
    acme = textwrap.dedent(
        """
            location /.well-known/acme-challenge/ {
                root /var/www/certbot;
            }
        """
    ).strip()

    ip_fallback = textwrap.dedent(
        f"""
        server {{
            listen 80 default_server;
            listen [::]:80 default_server;
            server_name _;
            {proxy}
        }}
        """
    ).strip()

    if not ssl:
        return textwrap.dedent(
            f"""
            server {{
                listen 80;
                listen [::]:80;
                server_name {DOMAIN} www.{DOMAIN};
                {acme}
                {proxy}
            }}

            {ip_fallback}
            """
        ).strip()

    return textwrap.dedent(
        f"""
        server {{
            listen 80;
            listen [::]:80;
            server_name {DOMAIN} www.{DOMAIN};
            {acme}
            location / {{
                return 301 https://$host$request_uri;
            }}
        }}

        server {{
            listen 443 ssl http2;
            listen [::]:443 ssl http2;
            server_name {DOMAIN} www.{DOMAIN};

            ssl_certificate /etc/letsencrypt/live/{DOMAIN}/fullchain.pem;
            ssl_certificate_key /etc/letsencrypt/live/{DOMAIN}/privkey.pem;
            include /etc/letsencrypt/options-ssl-nginx.conf;
            ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

            {proxy}
        }}

        {ip_fallback}
        """
    ).strip()
