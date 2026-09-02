#!/bin/bash
# Configura o Watchdog Inteligente de Busca e Reconexão Automática do Wi-Fi com Hotspot Fallback Rápido (12-18s)
# TV Box (SSV6051 / RK322x)

echo "Instalando script de watchdog em /usr/local/bin/wifi-watchdog.sh..."

cat << 'EOF' > /usr/local/bin/wifi-watchdog.sh
#!/bin/bash
# WiFi Intelligent Auto-Connect, Fallback Hotspot & Watchdog for Klipper OS TV Box (SSV6051 / RK322x)

HOTSPOT_NAME="Hotspot-Setup"
HOTSPOT_SSID="impressora"
HOTSPOT_PASS="impressora"
FAIL_COUNT=0
HOTSPOT_TIMER=0

create_hotspot_profile() {
    if ! nmcli connection show "$HOTSPOT_NAME" >/dev/null 2>&1; then
        nmcli connection add type wifi ifname wlan0 con-name "$HOTSPOT_NAME" autoconnect no ssid "$HOTSPOT_SSID" >/dev/null 2>&1
        nmcli connection modify "$HOTSPOT_NAME" 802-11-wireless.mode ap 802-11-wireless.band bg >/dev/null 2>&1
        nmcli connection modify "$HOTSPOT_NAME" 802-11-wireless-security.key-mgmt wpa-psk 802-11-wireless-security.psk "$HOTSPOT_PASS" >/dev/null 2>&1
        nmcli connection modify "$HOTSPOT_NAME" ipv4.method shared ipv4.addresses 192.168.4.1/24 >/dev/null 2>&1
    fi
}

create_hotspot_profile

while true; do
    CLIENT_CONN=$(nmcli -t -f NAME,TYPE connection show 2>/dev/null | grep ":802-11-wireless" | grep -v "$HOTSPOT_NAME" | head -n1 | cut -d: -f1)
    ACTIVE_CONN=$(nmcli -t -f NAME,DEVICE connection show --active 2>/dev/null | grep ":wlan0$" | cut -d: -f1)

    # 1. Se estiver conectado no Wi-Fi cliente (de casa)
    if [ -n "$ACTIVE_CONN" ] && [ "$ACTIVE_CONN" != "$HOTSPOT_NAME" ]; then
        GATEWAY=$(ip route show 2>/dev/null | awk '/default/ {print $3}' | head -n1)
        [ -z "$GATEWAY" ] && GATEWAY="192.168.31.1"

        if ping -c 1 -W 2 "$GATEWAY" >/dev/null 2>&1; then
            FAIL_COUNT=0
            HOTSPOT_TIMER=0
            sleep 10
            continue
        fi
    fi

    # 2. Se estiver operando em modo Ponto de Acesso (Hotspot 'impressora')
    if [ "$ACTIVE_CONN" = "$HOTSPOT_NAME" ]; then
        HOTSPOT_TIMER=$((HOTSPOT_TIMER + 1))

        # A cada ~18 segundos no Hotspot (6 ciclos de 3s), checar se a rede de casa voltou
        if [ $HOTSPOT_TIMER -ge 6 ]; then
            HOTSPOT_TIMER=0

            HAS_CLIENT=$(ip neigh show dev wlan0 2>/dev/null | grep -E "192\.168\.4\.[0-9]+" | grep -v "FAILED" | head -n1)

            if [ -z "$HAS_CLIENT" ] && [ -n "$CLIENT_CONN" ]; then
                TARGET_SSID=$(nmcli -g 802-11-wireless.ssid connection show "$CLIENT_CONN" 2>/dev/null)
                if [ -n "$TARGET_SSID" ]; then
                    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pausando Hotspot por 2s para verificar se a rede '$TARGET_SSID' voltou..."
                    nmcli connection down "$HOTSPOT_NAME" >/dev/null 2>&1 || true
                    sleep 1
                    nmcli device wifi rescan 2>/dev/null || true
                    sleep 1

                    if nmcli -t -f SSID dev wifi list 2>/dev/null | grep -Fqx "$TARGET_SSID"; then
                        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Rede '$TARGET_SSID' detectada! Reconectando no Wi-Fi de casa..."
                        nmcli connection up "$CLIENT_CONN" >/dev/null 2>&1 || true
                        FAIL_COUNT=0
                        sleep 5
                        continue
                    else
                        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Rede '$TARGET_SSID' ainda ausente. Reativando Hotspot '$HOTSPOT_SSID'..."
                        nmcli connection up "$HOTSPOT_NAME" >/dev/null 2>&1 || true
                    fi
                fi
            fi
        fi

        sleep 3
        continue
    fi

    # 3. Se estiver desconectado (procurando rede cliente)
    FAIL_COUNT=$((FAIL_COUNT + 1))

    TARGET_SSID=""
    if [ -n "$CLIENT_CONN" ]; then
        TARGET_SSID=$(nmcli -g 802-11-wireless.ssid connection show "$CLIENT_CONN" 2>/dev/null)
    fi

    nmcli device wifi rescan 2>/dev/null || true

    if [ -n "$TARGET_SSID" ] && nmcli -t -f SSID dev wifi list 2>/dev/null | grep -Fqx "$TARGET_SSID"; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Rede '$TARGET_SSID' detectada no ar! Conectando..."
        nmcli connection up "$CLIENT_CONN" >/dev/null 2>&1 || true
        FAIL_COUNT=0
        sleep 5
        continue
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sem conexao cliente (Tentativa #$FAIL_COUNT/4)..."

    # Apos 4 tentativas (~12 a 15 segundos sem achar rede cliente), sobe o Hotspot 'impressora'
    if [ $FAIL_COUNT -ge 4 ] || [ -z "$CLIENT_CONN" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Nenhuma rede Wi-Fi encontrada. Subindo Ponto de Acesso (Hotspot) '$HOTSPOT_SSID'..."
        create_hotspot_profile
        nmcli connection down "$CLIENT_CONN" 2>/dev/null || true
        nmcli connection up "$HOTSPOT_NAME" >/dev/null 2>&1 || true
        FAIL_COUNT=0
        HOTSPOT_TIMER=0
        sleep 3
        continue
    fi

    sleep 3
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

echo "Pronto! O Watchdog inteligente de Wi-Fi rápido (12s) está ativo e monitorando."
