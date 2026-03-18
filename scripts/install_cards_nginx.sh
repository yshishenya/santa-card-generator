#!/usr/bin/env bash

set -euo pipefail

DOMAIN="cards.pro-4.ru"
PROJECT_DIR="/opt/projects/cards"
FINAL_CONF_SRC="$PROJECT_DIR/nginx/$DOMAIN.conf"
NGINX_AVAILABLE="/etc/nginx/sites-available/$DOMAIN.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/$DOMAIN.conf"
ACME_WEBROOT="/var/www/certbot"
BOOTSTRAP_CONF="$(mktemp)"

cleanup() {
    rm -f "$BOOTSTRAP_CONF"
}

trap cleanup EXIT

if [[ "${EUID}" -ne 0 ]]; then
    echo "Run this script with sudo or as root." >&2
    exit 1
fi

if [[ ! -f "$FINAL_CONF_SRC" ]]; then
    echo "Missing nginx config template: $FINAL_CONF_SRC" >&2
    exit 1
fi

mkdir -p "$ACME_WEBROOT"

cat >"$BOOTSTRAP_CONF" <<EOF
upstream cards_frontend {
    server 127.0.0.1:3300;
    keepalive 32;
}

upstream cards_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    access_log /var/log/nginx/$DOMAIN.access.log;
    error_log /var/log/nginx/$DOMAIN.error.log;

    location /.well-known/acme-challenge/ {
        root $ACME_WEBROOT;
        default_type text/plain;
        try_files \$uri =404;
    }

    location /api/ {
        proxy_pass http://cards_backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://cards_backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
        access_log off;
    }

    location /docs {
        proxy_pass http://cards_backend/docs;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
    }

    location /openapi.json {
        proxy_pass http://cards_backend/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
    }

    location /redoc {
        proxy_pass http://cards_backend/redoc;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
    }

    location / {
        proxy_pass http://cards_frontend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

install -m 644 "$BOOTSTRAP_CONF" "$NGINX_AVAILABLE"
ln -sfn "$NGINX_AVAILABLE" "$NGINX_ENABLED"

echo "Testing bootstrap nginx config..."
nginx -t
systemctl reload nginx

if [[ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
    echo "Requesting Let's Encrypt certificate for $DOMAIN..."
    certbot certonly --webroot -w "$ACME_WEBROOT" -d "$DOMAIN"
else
    echo "Certificate already exists for $DOMAIN, skipping issuance."
fi

install -m 644 "$FINAL_CONF_SRC" "$NGINX_AVAILABLE"

echo "Testing final nginx config..."
nginx -t
systemctl reload nginx

echo "Verifying local upstreams..."
curl -fsS "http://127.0.0.1:8000/health" >/dev/null
curl -fsSI "http://127.0.0.1:3300" >/dev/null

echo "Done. Check:"
echo "  http://$DOMAIN"
echo "  https://$DOMAIN"
echo "  https://$DOMAIN/health"
