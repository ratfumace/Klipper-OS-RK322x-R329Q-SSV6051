#!/bin/bash
# Configura suporte simultâneo a HTTP (porta 80) e HTTPS (porta 443) no Nginx com certificado SSL auto-assinado.

echo "Gerando certificado SSL auto-assinado de 10 anos..."
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/ssl/private/nginx-selfsigned.key \
    -out /etc/ssl/certs/nginx-selfsigned.crt \
    -subj "/C=BR/ST=SP/L=Local/O=KlipperOS/OU=3DPrinting/CN=klipper-os"

echo "Atualizando configuração do Nginx (/etc/nginx/sites-available/default)..."

cat << 'EOF' > /etc/nginx/sites-available/default
# Default Nginx site configuration for Klipper OS (HTTP + HTTPS)
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;

    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    access_log /var/log/nginx/klipper-web-access.log;
    error_log /var/log/nginx/klipper-web-error.log;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 4;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    # Current Web Root (Mainsail by default)
    root /home/klipper/mainsail;
    index index.html;
    server_name _;

    client_max_body_size 0;
    proxy_request_buffering off;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location = /index.html {
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }

    location /websocket {
        proxy_pass http://127.0.0.1:7125/websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    location ~ ^/(printer|api|access|machine|server)/ {
        proxy_pass http://127.0.0.1:7125$request_uri;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_read_timeout 600;
    }
}
EOF

nginx -t && systemctl reload nginx
echo "Pronto! A interface web agora aceita conexões HTTP (porta 80) e HTTPS (porta 443)."
