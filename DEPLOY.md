# 问元 · 云服务器部署说明

> 目标环境：Ubuntu 22.04+ · 2C4G · Nginx + systemd  
> 架构说明见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 1. 服务器准备

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git
```

安全组放行 **22**、**80**、**443**（HTTPS 必须）。

> 若 `https://wenyuan.online` 超时但 HTTP 正常，请在 [轻量/云服务器防火墙](https://console.cloud.tencent.com/lighthouse) 添加入站规则：**TCP 443**，来源 `0.0.0.0/0`。

## 1.1 域名解析（wenyuan.online）

在 [腾讯云 DNS 解析](https://console.cloud.tencent.com/cns) 为 `wenyuan.online` 添加记录：

| 主机记录 | 记录类型 | 记录值 | 说明 |
|---------|---------|--------|------|
| `@` | A | `119.91.54.153` | 根域名 |
| `www` | A | `119.91.54.153` | 可选，www 子域 |

TTL 建议 **600**。生效通常几分钟到几小时。验证：

```bash
ping wenyuan.online
curl -sS http://wenyuan.online/health
```

## 1.2 HTTPS（Let's Encrypt）

DNS 生效且 **443 已放行** 后：

```bash
cd scripts
python setup_https.py 119.91.54.153 YOUR_PASSWORD admin@wenyuan.online
```

证书自动续期由 `certbot.timer` 负责。后续 `deploy_remote.py` 会检测证书并保留 HTTPS 配置。

## 2. 部署代码

**方式 A：本机 SFTP 上传（推荐，绕过 GitHub 超时）**

```bash
python scripts/deploy_remote.py YOUR_HOST YOUR_PASSWORD
```

**方式 B：服务器 git clone**

```bash
sudo mkdir -p /opt/wenyuan
sudo chown -R ubuntu:ubuntu /opt/wenyuan
git clone https://github.com/goodisok/wenyuan.git /opt/wenyuan
cd /opt/wenyuan
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 3. 环境变量

```bash
cp .env.example .env
nano .env
```

必填（AI 功能）：

```
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-v4-pro
AI_ENABLED=true
```

## 4. systemd 服务

`/etc/systemd/system/wenyuan.service`：

```ini
[Unit]
Description=Wenyuan FastAPI
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/wenyuan
EnvironmentFile=/opt/wenyuan/.env
ExecStart=/opt/wenyuan/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable wenyuan
sudo systemctl restart wenyuan
```

## 5. Nginx 反代

`/etc/nginx/sites-available/wenyuan`：

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name wenyuan.online www.wenyuan.online _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
    }

    location /static/ {
        alias /opt/wenyuan/static/;
        expires 7d;
    }
}
```

```bash
sudo ln -sf /etc/nginx/sites-available/wenyuan /etc/nginx/sites-enabled/wenyuan
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

## 6. HTTPS（可选）

使用 Certbot：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your.domain.com
```

## 7. 验证

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","version":"1.0.0"}
```

浏览器访问 `http://YOUR_IP/`，走通：排盘 → 分享链接 → L1 解读 → L2/L3 追问。

## 8. 更新部署

```bash
# SFTP 方式
python scripts/deploy_remote.py YOUR_HOST YOUR_PASSWORD

# 或 git pull + 重启
cd /opt/wenyuan && git pull && ./venv/bin/pip install -r requirements.txt
sudo systemctl restart wenyuan
```

## 9. 运维

| 操作 | 命令 |
|------|------|
| 查看日志 | `journalctl -u wenyuan -f` |
| 临时关闭 AI | `.env` 设 `AI_ENABLED=false` 后 `sudo systemctl restart wenyuan` |
| 健康检查 | `GET /health` |
