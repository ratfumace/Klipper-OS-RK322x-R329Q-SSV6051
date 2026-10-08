#!/bin/bash
# Configura o Watchdog Inteligente de Reconexão Contínua do Wi-Fi na TV Box (SSV6051 / RK322x)
# Mantém o Wi-Fi sempre conectado sem derrubar conexões saudáveis e sem modo hotspot.

echo "Instalando script de watchdog em /usr/local/bin/wifi-watchdog.sh..."

cat << 'EOF' > /usr/local/bin/wifi-watchdog.sh
#!/bin/bash
# WiFi Intelligent Auto-Reconnect & Watchdog for Klipper OS TV Box (SSV6051 / RK322x)
# Resiliente contra jitter e latencia do chip SSV6051. Nunca derruba conexoes estaveis.

FAIL_COUNT=0
BOOT_GRACE=45

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando WiFi Watchdog. Aguardando ${BOOT_GRACE}s de carencia inicial..."
sleep "$BOOT_GRACE"

while true; do
    ETH_STATE=$(nmcli -t -f DEVICE,STATE dev 2>/dev/null | grep "^eth0:" | cut -d: -f2)
    WLAN_STATE=$(nmcli -t -f DEVICE,STATE dev 2>/dev/null | grep "^wlan0:" | cut -d: -f2)

    CLIENT_CONN=$(nmcli -t -f NAME,TYPE connection show 2>/dev/null | grep ":802-11-wireless" | head -n1 | cut -d: -f1)
    [ -z "$CLIENT_CONN" ] && CLIENT_CONN="KlipperOS WiFi"

    # Garante compatibilidade do chip SSV6051 com roteadores WPA2/WPA3 (evita rejeicao por PMF/802.11w)
    nmcli connection modify "$CLIENT_CONN" 802-11-wireless-security.pmf disable 802-11-wireless-security.proto rsn 2>/dev/null || true

    if [ "$WLAN_STATE" = "connected" ]; then
        if [ "$ETH_STATE" = "connected" ]; then
            FAIL_COUNT=0
            sleep 20
            continue
        fi

        GATEWAY=$(ip route show dev wlan0 2>/dev/null | awk '/default/ {print $3}' | head -n1)
        [ -z "$GATEWAY" ] && GATEWAY="192.168.31.1"

        IS_ALIVE=0
        if ping -I wlan0 -c 3 -W 3 "$GATEWAY" >/dev/null 2>&1; then
            IS_ALIVE=1
        elif ping -I wlan0 -c 2 -W 3 "1.1.1.1" >/dev/null 2>&1; then
            IS_ALIVE=1
        elif ping -I wlan0 -c 2 -W 3 "8.8.8.8" >/dev/null 2>&1; then
            IS_ALIVE=1
        fi

        if [ "$IS_ALIVE" -eq 1 ]; then
            if [ "$FAIL_COUNT" -gt 0 ]; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] Conexao wlan0 restabelecida com sucesso."
            fi
            FAIL_COUNT=0
            sleep 20
            continue
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Aviso: Sem resposta no gateway/DNS via wlan0 ($FAIL_COUNT/12)..."

            if [ $FAIL_COUNT -ge 12 ]; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] wlan0 sem resposta ha mais de 3 minutos. Tentando reconectar..."
                nmcli connection up "$CLIENT_CONN" >/dev/null 2>&1 || {
                    nmcli device disconnect wlan0 >/dev/null 2>&1 || true
                    sleep 3
                    nmcli connection up "$CLIENT_CONN" >/dev/null 2>&1 || true
                }
                FAIL_COUNT=0
                sleep 20
            else
                sleep 15
            fi
            continue
        fi
    fi

    if [ "$WLAN_STATE" = "connecting" ] || [ "$WLAN_STATE" = "need-auth" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] wlan0 negociando conexao ($WLAN_STATE)... aguardando."
        sleep 10
        continue
    fi

    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] wlan0 desconectada (Tentativa #$FAIL_COUNT). Conectando Wi-Fi..."

    nmcli connection up "$CLIENT_CONN" >/dev/null 2>&1 || true

    if [ $FAIL_COUNT -ge 20 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Mais de 5 minutos sem sinal. Reiniciando subsistema de rede..."
        systemctl restart NetworkManager 2>/dev/null || true
        FAIL_COUNT=0
        sleep 15
    fi

    sleep 15
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
