#!/bin/bash
# ==============================================================================
# Script de Atualização OTA (1-Clique) do Klipper OS RK322x
# Atualiza os scripts de sistema, portal web e componentes a partir do GitHub.
# ==============================================================================

LOG_FILE="/var/log/klipper_os_update.log"
mkdir -p /var/log
exec > >(tee "$LOG_FILE") 2>&1

echo "=================================================="
echo "Iniciando Atualização do Klipper OS: $(date)"
echo "=================================================="

REPO_RAW="https://raw.githubusercontent.com/ratfumace/Klipper-OS-RK322x-R329Q-SSV6051/main"
TMP_DIR="/tmp/klipper_os_update_$$"
mkdir -p "$TMP_DIR"
cd "$TMP_DIR"

echo "[1/4] Consultando versão mais recente no GitHub..."
REMOTE_INFO=$(curl -s -m 15 -H "User-Agent: KlipperOS-Updater/1.0" "https://api.github.com/repos/ratfumace/Klipper-OS-RK322x-R329Q-SSV6051/commits/main" || true)

COMMIT_SHA=$(echo "$REMOTE_INFO" | grep -o '"sha": *"[^"]*"' | head -n 1 | cut -d'"' -f4)
COMMIT_DATE=$(echo "$REMOTE_INFO" | grep -o '"date": *"[^"]*"' | head -n 1 | cut -d'"' -f4)
COMMIT_MSG=$(echo "$REMOTE_INFO" | grep -m 1 -o '"message": *"[^"]*"' | cut -d'"' -f4)

if [ -z "$COMMIT_SHA" ]; then
    COMMIT_SHA="latest"
    COMMIT_DATE="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    COMMIT_MSG="Atualização manual do Klipper OS"
fi

echo "Commit detectado: $COMMIT_SHA ($COMMIT_DATE)"
echo "Mensagem: $COMMIT_MSG"

echo "[2/4] Baixando wifi_portal_server.py atualizado..."
if curl -sSL -m 30 "$REPO_RAW/tudo_que_foi_usado/wifi_portal_server.py" -o wifi_portal_server.py; then
    if python3 -m py_compile wifi_portal_server.py; then
        echo "Validação de sintaxe OK. Atualizando /usr/local/bin/wifi_portal_server.py..."
        cp wifi_portal_server.py /usr/local/bin/wifi_portal_server.py
        chmod +x /usr/local/bin/wifi_portal_server.py
        if [ -d "/home/klipper/tudo_que_foi_usado" ]; then
            cp wifi_portal_server.py /home/klipper/tudo_que_foi_usado/wifi_portal_server.py 2>/dev/null || true
            chown klipper:klipper /home/klipper/tudo_que_foi_usado/wifi_portal_server.py 2>/dev/null || true
        fi
    else
        echo "ERRO: O arquivo baixado contém erros de sintaxe. Abortando substituição do portal."
        exit 1
    fi
else
    echo "ERRO: Falha ao baixar wifi_portal_server.py do GitHub."
    exit 1
fi

echo "[3/4] Atualizando scripts em /home/klipper/tudo_que_foi_usado/..."
mkdir -p /home/klipper/tudo_que_foi_usado/
for SCRIPT in 01_fix_wifi_powersave.sh 02_expand_root_partition.sh 03_setup_wifi_watchdog.sh 04_setup_ssl_https.sh 05_setup_wifi_portal.sh 06_klipper_os_updater.sh; do
    echo "  -> Baixando $SCRIPT..."
    curl -sSL -m 20 "$REPO_RAW/tudo_que_foi_usado/$SCRIPT" -o "/home/klipper/tudo_que_foi_usado/$SCRIPT" 2>/dev/null || true
    chmod +x "/home/klipper/tudo_que_foi_usado/$SCRIPT" 2>/dev/null || true
    chown klipper:klipper "/home/klipper/tudo_que_foi_usado/$SCRIPT" 2>/dev/null || true
done
cp /home/klipper/tudo_que_foi_usado/06_klipper_os_updater.sh /usr/local/bin/klipper_os_updater.sh 2>/dev/null || true
chmod +x /usr/local/bin/klipper_os_updater.sh 2>/dev/null || true

# Garantir patches de Creality Cloud se OctoPrint estiver instalado
if [ -d "/home/klipper/OctoPrint/venv" ]; then
    echo "Verificando patches do plugin Creality Cloud..."
    python3 -c "
import re, json
tb_path = '/home/klipper/OctoPrint/venv/lib/python3.9/site-packages/octoprint_crealitycloud/crealitytb.py'
cc_path = '/home/klipper/OctoPrint/venv/lib/python3.9/site-packages/octoprint_crealitycloud/crealitycloud.py'
helper_code = '''
def get_cloud_model():
    try:
        import json
        with open(\"/home/klipper/.octoprint/data/crealitycloud/config.json\") as _f:
            _c = json.load(_f)
            return _c.get(\"model\", \"Ender-3 V3 SE\")
    except Exception:
        return \"Ender-3 V3 SE\"

def get_local_ip():
    try:
        import socket
        _s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _s.connect((\"8.8.8.8\", 80))
        _ip = _s.getsockname()[0]
        _s.close()
        return _ip
    except Exception:
        return \"127.0.0.1\"
'''
try:
    with open(tb_path) as f: tb = f.read()
    if 'def get_cloud_model():' not in tb: tb = helper_code + '\n' + tb
    tb = re.sub(r'\"netIP\":\s*\"[^\"]*\"', '\"netIP\": get_local_ip()', tb)
    tb = re.sub(r'\"model\":\s*\"[^\"]*\"', '\"model\": get_cloud_model()', tb)
    with open(tb_path, 'w') as f: f.write(tb)

    with open(cc_path) as f: cc = f.read()
    if 'def get_cloud_model():' not in cc: cc = helper_code + '\n' + cc
    cc = re.sub(r'self\._aliprinter\.model\s*=\s*\"[^\"]*\"', 'self._aliprinter.model = get_cloud_model()', cc)
    cc = re.sub(r'self\._aliprinter\._attributes_msg\[\"netIP\"\]\s*=\s*\"[^\"]*\"', 'self._aliprinter._attributes_msg[\"netIP\"] = get_local_ip()', cc)
    with open(cc_path, 'w') as f: f.write(cc)
    print('Patches aplicados com sucesso!')
except Exception as e:
    print('Nota de patches:', e)
" 2>/dev/null || true
    systemctl restart octoprint.service 2>/dev/null || true
fi

# Salvar metadados da versao local
cat << VERSION_EOF > /etc/klipper-os-version.json
{
  "commit_sha": "$COMMIT_SHA",
  "commit_date": "$COMMIT_DATE",
  "commit_message": "$COMMIT_MSG",
  "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
VERSION_EOF

echo "[4/4] Finalizando atualização..."
rm -rf "$TMP_DIR"
echo "=================================================="
echo "Atualização concluída com sucesso em $(date)!"
echo "STATUS: SUCCESS"
echo "=================================================="

# Reiniciar o portal em segundo plano
(sleep 2 && systemctl restart wifi-portal.service) &
