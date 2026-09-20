#!/bin/bash
# Configura o Servidor Web de Configuração Wi-Fi (impressora.local e /wifi)
# Interface web elegante em tema escuro para gerenciar redes Wi-Fi e configurar IP (DHCP ou Estático).

echo "Instalando dependências de mDNS..."
DEBIAN_FRONTEND=noninteractive apt-get update >/dev/null 2>&1
DEBIAN_FRONTEND=noninteractive apt-get install -y avahi-daemon libnss-mdns >/dev/null 2>&1

echo "Configurando hostname e mDNS..."
hostnamectl set-hostname impressora 2>/dev/null || hostname impressora
echo "impressora" > /etc/hostname
cat << 'HOSTS_EOF' > /etc/hosts
127.0.0.1   localhost impressora klipper-os
::1         localhost ip6-localhost ip6-loopback
fe00::0     ip6-localnet
ff00::0     ip6-mcastprefix
ff02::1     ip6-allnodes
ff02::2     ip6-allrouters
HOSTS_EOF

systemctl restart avahi-daemon

echo "Instalando servidor web do Portal em /usr/local/bin/wifi_portal_server.py..."
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cp "$DIR/wifi_portal_server.py" 2>/dev/null || cp /tmp/wifi_portal_server.py /usr/local/bin/wifi_portal_server.py 2>/dev/null || true
chmod +x /usr/local/bin/wifi_portal_server.py

cat << 'SVC_EOF' > /etc/systemd/system/wifi-portal.service
[Unit]
Description=WiFi Setup Portal Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/bin/wifi_portal_server.py
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
SVC_EOF

systemctl daemon-reload
systemctl enable wifi-portal.service
systemctl restart wifi-portal.service

echo "Pronto! O Portal de configuração Wi-Fi está instalado e ativo em impressora.local."
