#!/bin/bash
# Configura o Portal de Configuração Wi-Fi (Captive Portal) e Ponto de Acesso de Recuperação
# Tema escuro elegante em verde/vermelho/preto, com escolha de IP (DHCP ou Estático) e resolução impressora.local.

echo "Instalando dependências de rede e mDNS..."
DEBIAN_FRONTEND=noninteractive apt-get update >/dev/null 2>&1
DEBIAN_FRONTEND=noninteractive apt-get install -y dnsmasq-base iw wireless-tools iptables avahi-daemon libnss-mdns >/dev/null 2>&1

echo "Configurando hostname e mDNS..."
hostnamectl set-hostname impressora 2>/dev/null || hostname impressora
echo "impressora" > /etc/hostname
cat << 'EOF' > /etc/hosts
127.0.0.1   localhost impressora klipper-os
::1         localhost ip6-localhost ip6-loopback
fe00::0     ip6-localnet
ff00::0     ip6-mcastprefix
ff02::1     ip6-allnodes
ff02::2     ip6-allrouters
EOF

systemctl restart avahi-daemon

echo "Instalando servidor web do Portal em /usr/local/bin/wifi_portal_server.py..."
cp /tmp/wifi_portal_server.py /usr/local/bin/wifi_portal_server.py 2>/dev/null || true
chmod +x /usr/local/bin/wifi_portal_server.py

cat << 'EOF' > /etc/systemd/system/wifi-portal.service
[Unit]
Description=WiFi Setup Captive Portal Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/bin/wifi_portal_server.py
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable wifi-portal.service
systemctl restart wifi-portal.service

echo "Pronto! O Portal de configuração Wi-Fi está instalado e ativo."
