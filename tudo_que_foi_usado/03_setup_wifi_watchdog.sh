#!/bin/bash
# Configura o Watchdog de Reconexão Automática do Wi-Fi na TV Box (SSV6051 / RK322x)
# Se o roteador reiniciar ou a rede cair, o sistema reconecta sozinho sem precisar tirar da tomada.

echo "Instalando script de watchdog em /usr/local/bin/wifi-watchdog.sh..."

cat << 'EOF' > /usr/local/bin/wifi-watchdog.sh
#!/bin/bash
# WiFi Auto-Reconnect Watchdog for Klipper OS TV Box (SSV6051 / RK322x)

FAILURES=0

while true; do
    GATEWAY=$(ip route show 2>/dev/null | awk '/default/ {print $3}' | head -n1)
    if [ -z "$GATEWAY" ]; then
        GATEWAY="192.168.31.1"
    fi

    WLAN_STATE=$(nmcli -t -f DEVICE,STATE dev 2>/dev/null | grep "^wlan0:" | cut -d: -f2)

    IS_OK=0
    if [ "$WLAN_STATE" = "connected" ]; then
        if ping -c 1 -W 3 "$GATEWAY" >/dev/null 2>&1; then
            IS_OK=1
        fi
    fi

    if [ $IS_OK -eq 1 ]; then
        if [ $FAILURES -gt 0 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] WiFi connection restored!"
        fi
        FAILURES=0
    else
        FAILURES=$((FAILURES + 1))
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] WiFi lost or unreachable (Failure #$FAILURES, Gateway: $GATEWAY, State: $WLAN_STATE)..."

        CONN_NAME=$(nmcli -t -f NAME,TYPE connection show 2>/dev/null | grep ":802-11-wireless" | head -n1 | cut -d: -f1)
        [ -z "$CONN_NAME" ] && CONN_NAME="KlipperOS WiFi"

        if [ $FAILURES -eq 1 ] || [ $FAILURES -eq 2 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Trying nmcli connection up..."
            nmcli connection up "$CONN_NAME" >/dev/null 2>&1 || true
        elif [ $FAILURES -eq 3 ] || [ $FAILURES -eq 4 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cycling WiFi radio..."
            nmcli radio wifi off >/dev/null 2>&1
            sleep 2
            nmcli radio wifi on >/dev/null 2>&1
            sleep 3
            nmcli connection up "$CONN_NAME" >/dev/null 2>&1 || true
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Resetting wlan0 interface and restarting NetworkManager..."
            ip link set wlan0 down >/dev/null 2>&1
            sleep 2
            ip link set wlan0 up >/dev/null 2>&1
            systemctl restart NetworkManager >/dev/null 2>&1
            sleep 5
            nmcli connection up "$CONN_NAME" >/dev/null 2>&1 || true
            FAILURES=1
        fi
    fi

    sleep 15
done
EOF

chmod +x /usr/local/bin/wifi-watchdog.sh

echo "Criando serviço systemd wifi-watchdog.service..."

cat << 'EOF' > /etc/systemd/system/wifi-watchdog.service
[Unit]
Description=WiFi Auto-Reconnect Watchdog
After=network.target NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=simple
ExecStart=/usr/local/bin/wifi-watchdog.sh
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable wifi-watchdog.service
systemctl restart wifi-watchdog.service

echo "Pronto! O Watchdog de Wi-Fi está ativo e monitorando a conexão."
