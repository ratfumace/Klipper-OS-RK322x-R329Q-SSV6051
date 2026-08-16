#!/bin/bash
# Desativa a economia de energia do Wi-Fi para evitar desconexoes na TV Box

echo "Desativando powersave do Wi-Fi no NetworkManager..."

echo "[connection]" > /etc/NetworkManager/conf.d/default-wifi-powersave-on.conf
echo "wifi.powersave = 2" >> /etc/NetworkManager/conf.d/default-wifi-powersave-on.conf

systemctl restart NetworkManager

echo "Pronto! O Wi-Fi não irá mais dormir."
