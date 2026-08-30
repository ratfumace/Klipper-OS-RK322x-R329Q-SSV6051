#!/bin/bash
# Configura o Watchdog de Busca Infinita e Reconexão Automática do Wi-Fi na TV Box (SSV6051 / RK322x)
# Mantém a TV Box buscando o sinal de Wi-Fi infinitamente, mesmo se ligada antes do roteador.

echo "Instalando script de busca infinita de Wi-Fi em /usr/local/bin/wifi-watchdog.sh..."

cat << 'EOF' > /usr/local/bin/wifi-watchdog.sh
#!/bin/bash
# WiFi Infinite Auto-Connect & Watchdog for Klipper OS TV Box (SSV6051 / RK322x)
# Mantem a TV Box buscando o sinal de Wi-Fi infinitamente, mesmo se ligada antes do roteador.

FAIL_CYCLES=0

while true; do
    CONN_NAME=$(nmcli -t -f NAME,TYPE connection show 2>/dev/null | grep ":802-11-wireless" | head -n1 | cut -d: -f1)
    [ -z "$CONN_NAME" ] && CONN_NAME="KlipperOS WiFi"

    WLAN_STATE=$(nmcli -t -f DEVICE,STATE dev 2>/dev/null | grep "^wlan0:" | cut -d: -f2)

    IS_ONLINE=0
    if [ "$WLAN_STATE" = "connected" ]; then
        GATEWAY=$(ip route show 2>/dev/null | awk '/default/ {print $3}' | head -n1)
        [ -z "$GATEWAY" ] && GATEWAY="192.168.31.1"

        if ping -c 1 -W 2 "$GATEWAY" >/dev/null 2>&1; then
            IS_ONLINE=1
        fi
    fi

    if [ $IS_ONLINE -eq 1 ]; then
        if [ $FAIL_CYCLES -gt 0 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Wi-Fi conectado e operando com sucesso!"
        fi
        FAIL_CYCLES=0
        sleep 15
        continue
    fi

    FAIL_CYCLES=$((FAIL_CYCLES + 1))
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Buscando Wi-Fi no ar (Tentativa #$FAIL_CYCLES)..."

    # Forçar varredura no ar para detectar redes sem derrubar os serviços
    nmcli device wifi rescan 2>/dev/null || true
    nmcli connection up "$CONN_NAME" >/dev/null 2>&1 || true

    # Recuperação profunda apenas se passar mais de 5 minutos ininterruptos travado (30 ciclos de 10s)
    if [ $FAIL_CYCLES -ge 30 ] && [ $((FAIL_CYCLES % 30)) -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sem sinal ha mais de 5 minutos. Reiniciando NetworkManager..."
        systemctl reset-failed NetworkManager 2>/dev/null || true
        systemctl restart NetworkManager 2>/dev/null || true
        sleep 5
    fi

    sleep 10
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

echo "Pronto! O Watchdog de busca infinita de Wi-Fi está ativo e monitorando a conexão."
