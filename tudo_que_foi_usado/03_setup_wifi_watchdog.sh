#!/bin/bash
# Configura o Watchdog Inteligente de Reconexão Contínua do Wi-Fi na TV Box (SSV6051 / RK322x)
# Mantém o Wi-Fi sempre conectado sem derrubar conexões saudáveis e sem modo hotspot.

echo "Instalando script de watchdog em /usr/local/bin/wifi-watchdog.sh..."

cat << 'EOF' > /usr/local/bin/wifi-watchdog.sh
#!/bin/bash
# WiFi Intelligent Auto-Reconnect & Watchdog for Klipper OS TV Box (SSV6051 / RK322x)
# Mantem o Wi-Fi sempre conectado sem derrubar conexoes saudaveis e sem modo hotspot.

FAIL_COUNT=0

while true; do
    ETH_STATE=$(nmcli -t -f DEVICE,STATE dev 2>/dev/null | grep "^eth0:" | cut -d: -f2)
    WLAN_STATE=$(nmcli -t -f DEVICE,STATE dev 2>/dev/null | grep "^wlan0:" | cut -d: -f2)

    CLIENT_CONN=$(nmcli -t -f NAME,TYPE connection show 2>/dev/null | grep ":802-11-wireless" | head -n1 | cut -d: -f1)
    [ -z "$CLIENT_CONN" ] && CLIENT_CONN="KlipperOS WiFi"

    # 1. Se wlan0 ja estiver conectada
    if [ "$WLAN_STATE" = "connected" ]; then
        # Se o cabo ethernet tambem estiver conectado, nao precisa se preocupar
        if [ "$ETH_STATE" = "connected" ]; then
            FAIL_COUNT=0
            sleep 15
            continue
        fi

        # Testar conectividade via wlan0 com 3 pings e timeout de 2s
        GATEWAY=$(ip route show dev wlan0 2>/dev/null | awk '/default/ {print $3}' | head -n1)
        [ -z "$GATEWAY" ] && GATEWAY="192.168.31.1"

        if ping -I wlan0 -c 3 -W 2 "$GATEWAY" >/dev/null 2>&1; then
            FAIL_COUNT=0
            sleep 15
            continue
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Falha de ping no gateway $GATEWAY via wlan0 ($FAIL_COUNT/5)..."

            # Apenas se falhar 5 vezes consecutivas (~1 minuto de silencio total)
            if [ $FAIL_COUNT -ge 5 ]; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] Conexao wlan0 sem resposta ha mais de 1 minuto. Reconectando..."
                nmcli device disconnect wlan0 >/dev/null 2>&1 || true
                sleep 2
                nmcli connection up "$CLIENT_CONN" >/dev/null 2>&1 || true
                FAIL_COUNT=0
                sleep 15
            else
                sleep 10
            fi
            continue
        fi
    fi

    # 2. Se wlan0 estiver em processo de conexao / autenticacao
    if [ "$WLAN_STATE" = "connecting" ] || [ "$WLAN_STATE" = "need-auth" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] wlan0 em negociacao ($WLAN_STATE)... aguardando."
        sleep 10
        continue
    fi

    # 3. Se wlan0 estiver desconectada (disconnected / unavailable)
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] wlan0 desconectada (Tentativa #$FAIL_COUNT). Buscando Wi-Fi..."

    nmcli device wifi rescan 2>/dev/null || true
    sleep 3
    nmcli connection up "$CLIENT_CONN" >/dev/null 2>&1 || true

    # Se passar de 5 minutos ininterruptos travado (20 ciclos de 15s)
    if [ $FAIL_COUNT -ge 20 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Mais de 5 minutos sem sinal. Reiniciando NetworkManager..."
        systemctl restart NetworkManager 2>/dev/null || true
        FAIL_COUNT=0
        sleep 10
    fi

    sleep 12
done
EOF

chmod +x /usr/local/bin/wifi-watchdog.sh

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

echo "Pronto! O Watchdog inteligente de Wi-Fi contínuo está ativo e monitorando."
