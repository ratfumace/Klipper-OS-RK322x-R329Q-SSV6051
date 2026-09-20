#!/usr/bin/env python3
import http.server
import socketserver
import json
import subprocess
import urllib.parse
import os
import re
import time
import threading

PORT = 8088

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configuração Wi-Fi - Klipper OS</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; }
        body { background: #090a0f; color: #f4f4f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px 14px; }
        .card { background: #14151c; border: 1px solid #272730; border-radius: 18px; padding: 28px 24px; width: 100%; max-width: 440px; box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.8); }
        .header { text-align: center; margin-bottom: 22px; }
        .header h1 { font-size: 22px; font-weight: 700; color: #10b981; letter-spacing: -0.5px; margin-bottom: 4px; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .header p { font-size: 13px; color: #a1a1aa; }
        
        .status-panel { background: #1c1d26; border: 1px solid #2e2f3d; border-radius: 12px; padding: 14px; margin-bottom: 20px; font-size: 13px; }
        .status-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .status-row:last-child { margin-bottom: 0; }
        .status-label { color: #a1a1aa; }
        .status-val { font-weight: 600; color: #f4f4f5; display: flex; align-items: center; gap: 6px; }
        .badge-green { background: #064e3b; color: #34d399; border: 1px solid #059669; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; }
        .badge-red { background: #7f1d1d; color: #fca5a5; border: 1px solid #dc2626; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; }
        .badge-yellow { background: #78350f; color: #fcd34d; border: 1px solid #d97706; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; }

        .form-group { margin-bottom: 16px; }
        label { display: block; font-size: 13px; font-weight: 600; color: #d4d4d8; margin-bottom: 6px; }
        .label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        select, input[type="text"], input[type="password"] { width: 100%; padding: 12px 14px; background: #0a0b10; border: 1px solid #333442; border-radius: 10px; color: #ffffff; font-size: 14px; outline: none; transition: border-color 0.2s, box-shadow 0.2s; }
        select:focus, input:focus { border-color: #10b981; box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2); }
        
        .ip-tabs { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: #0a0b10; padding: 4px; border-radius: 10px; border: 1px solid #272730; margin-bottom: 14px; }
        .ip-tab { padding: 8px; text-align: center; font-size: 13px; font-weight: 600; border-radius: 7px; cursor: pointer; color: #a1a1aa; transition: all 0.2s; user-select: none; }
        .ip-tab.active { background: #1c1d26; color: #10b981; border: 1px solid #10b981; }

        .btn-green { width: 100%; padding: 13px; background: linear-gradient(135deg, #059669, #10b981); color: white; border: none; border-radius: 10px; font-size: 15px; font-weight: 700; cursor: pointer; transition: transform 0.1s, opacity 0.2s; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); }
        .btn-green:hover { opacity: 0.95; }
        .btn-green:active { transform: scale(0.98); }
        .btn-green:disabled { background: #272730; color: #71717a; box-shadow: none; cursor: not-allowed; }

        .btn-secondary { width: 100%; padding: 11px; background: #1c1d26; color: #e4e4e7; border: 1px solid #333442; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s, border-color 0.2s; margin-top: 10px; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .btn-secondary:hover { background: #272730; border-color: #52525b; color: white; }

        .refresh-btn { background: #1c1d26; border: 1px solid #333442; color: #a1a1aa; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
        .refresh-btn:hover { color: #f4f4f5; border-color: #10b981; }

        .status-box { display: none; margin-top: 16px; padding: 14px; border-radius: 10px; font-size: 13px; text-align: center; line-height: 1.5; }
        .status-box.loading { display: block; background: #1c1d26; border: 1px solid #10b981; color: #f4f4f5; }
        .status-box.success { display: block; background: #064e3b; border: 1px solid #10b981; color: #f4f4f5; }
        .status-box.error { display: block; background: #7f1d1d; border: 1px solid #ef4444; color: #f4f4f5; }

        .footer { text-align: center; margin-top: 22px; font-size: 12px; color: #71717a; }
        .footer a { color: #10b981; text-decoration: none; }
        .password-container { position: relative; }
        .toggle-pw { position: absolute; right: 12px; top: 12px; background: none; border: none; color: #a1a1aa; cursor: pointer; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>🖨️ Klipper OS Wi-Fi</h1>
            <p>Gerenciamento de Rede e Conexão da Impressora</p>
        </div>

        <!-- Painel de Status em Tempo Real -->
        <div class="status-panel">
            <div class="status-row">
                <span class="status-label">Status da Conexão:</span>
                <span class="status-val" id="curStatus"><span class="badge-yellow">Verificando...</span></span>
            </div>
            <div class="status-row">
                <span class="status-label">Rede Conectada:</span>
                <span class="status-val" id="curSSID">--</span>
            </div>
            <div class="status-row">
                <span class="status-label">Endereço IP Atual:</span>
                <span class="status-val" id="curIP">--</span>
            </div>
        </div>

        <form id="wifiForm">
            <!-- Seleção de Rede -->
            <div class="form-group">
                <div class="label-row">
                    <label for="ssidSelect">Escolher Rede Wi-Fi</label>
                    <button type="button" class="refresh-btn" id="refreshBtn" onclick="fetchNetworks()">🔄 Escanear</button>
                </div>
                <select id="ssidSelect" onchange="handleSelectChange()">
                    <option value="">Escaneando redes no ar...</option>
                </select>
                <input type="text" id="ssidManual" placeholder="Digite o nome (SSID) da rede oculta..." style="display: none; margin-top: 8px;">
            </div>

            <!-- Senha -->
            <div class="form-group">
                <label for="password">Senha da Rede</label>
                <div class="password-container">
                    <input type="password" id="password" placeholder="Digite a senha do Wi-Fi..." autocomplete="current-password">
                    <button type="button" class="toggle-pw" onclick="togglePassword()">👁️</button>
                </div>
            </div>

            <!-- Escolha de Modo de IP -->
            <div class="form-group">
                <label>Configuração de IP</label>
                <div class="ip-tabs">
                    <div class="ip-tab active" id="tabDhcp" onclick="setIpMode('dhcp')">⚡ DHCP Automático</div>
                    <div class="ip-tab" id="tabStatic" onclick="setIpMode('static')">⚙️ IP Fixo / Estático</div>
                </div>

                <div id="staticFields" style="display: none;">
                    <div class="form-group">
                        <label for="staticIp">Endereço IP Desejado</label>
                        <input type="text" id="staticIp" placeholder="Ex: 192.168.31.100">
                    </div>
                    <div class="form-group">
                        <label for="staticGateway">Gateway (Roteador)</label>
                        <input type="text" id="staticGateway" placeholder="Ex: 192.168.31.1">
                    </div>
                    <div class="form-group">
                        <label for="staticDns">Servidores DNS</label>
                        <input type="text" id="staticDns" value="1.1.1.1, 8.8.8.8" placeholder="Ex: 1.1.1.1, 8.8.8.8">
                    </div>
                </div>
            </div>

            <button type="submit" class="btn-green" id="submitBtn">Salvar e Conectar Impressora</button>
        </form>

        <div id="statusBox" class="status-box"></div>

        <!-- Botão de Acesso Direto ao Mainsail -->
        <a id="mainsailLink" href="/" class="btn-secondary">
            🚀 Abrir Painel Mainsail
        </a>

        <div class="footer">
            Klipper OS RK322x • <a href="http://impressora.local">impressora.local</a>
        </div>
    </div>

    <script>
        let currentIpMode = 'dhcp';

        function setIpMode(mode) {
            currentIpMode = mode;
            document.getElementById('tabDhcp').className = mode === 'dhcp' ? 'ip-tab active' : 'ip-tab';
            document.getElementById('tabStatic').className = mode === 'static' ? 'ip-tab active' : 'ip-tab';
            document.getElementById('staticFields').style.display = mode === 'static' ? 'block' : 'none';
        }

        function togglePassword() {
            const pw = document.getElementById('password');
            pw.type = pw.type === 'password' ? 'text' : 'password';
        }

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                const curStatus = document.getElementById('curStatus');
                const curSSID = document.getElementById('curSSID');
                const curIP = document.getElementById('curIP');
                const mainsailLink = document.getElementById('mainsailLink');

                if (data.is_hotspot) {
                    curStatus.innerHTML = '<span class="badge-red">📡 Ponto de Acesso (Hotspot)</span>';
                    curSSID.textContent = 'impressora (Ponto de Acesso)';
                    curIP.textContent = '192.168.4.1';
                    mainsailLink.style.display = 'none';
                } else if (data.connected && data.ip) {
                    curStatus.innerHTML = '<span class="badge-green">🟢 Conectado</span>';
                    curSSID.textContent = `${data.ssid} (📶 ${data.signal}%)`;
                    curIP.innerHTML = `<strong>${data.ip}</strong>`;
                    mainsailLink.href = `http://${data.ip}`;
                    mainsailLink.style.display = 'flex';
                    
                    if (!document.getElementById('staticIp').value && data.ip) {
                        document.getElementById('staticIp').value = data.ip;
                    }
                    if (!document.getElementById('staticGateway').value && data.gateway) {
                        document.getElementById('staticGateway').value = data.gateway;
                    }
                } else {
                    curStatus.innerHTML = '<span class="badge-yellow">🟡 Desconectado</span>';
                    curSSID.textContent = 'Buscando rede...';
                    curIP.textContent = '--';
                }
            } catch (e) {
                console.error('Status fetch error:', e);
            }
        }

        async function fetchNetworks() {
            const btn = document.getElementById('refreshBtn');
            const select = document.getElementById('ssidSelect');
            btn.disabled = true;
            btn.textContent = 'Buscando...';
            select.innerHTML = '<option value="">Escaneando redes no ar...</option>';

            try {
                const res = await fetch('/api/scan');
                const networks = await res.json();
                select.innerHTML = '<option value="">-- Selecione sua rede Wi-Fi --</option>';
                
                if (!networks || networks.length === 0) {
                    select.innerHTML += '<option value="">Nenhuma rede detectada</option>';
                } else {
                    networks.forEach(net => {
                        const opt = document.createElement('option');
                        opt.value = net.ssid;
                        const signalPercent = net.signal > 75 ? '100%' : (net.signal > 50 ? '75%' : '50%');
                        const lock = (net.security && net.security !== '--') ? '🔒' : '🔓';
                        opt.textContent = `${net.ssid} (📶 ${signalPercent} ${lock})`;
                        select.appendChild(opt);
                    });
                }
                select.innerHTML += '<option value="__manual__">➕ Digitar rede oculta manualmente...</option>';
            } catch (err) {
                select.innerHTML = '<option value="">Erro ao buscar redes</option><option value="__manual__">➕ Digitar rede manual...</option>';
            } finally {
                btn.disabled = false;
                btn.textContent = '🔄 Escanear';
            }
        }

        function handleSelectChange() {
            const select = document.getElementById('ssidSelect');
            const manualInput = document.getElementById('ssidManual');
            if (select.value === '__manual__') {
                manualInput.style.display = 'block';
                manualInput.focus();
            } else {
                manualInput.style.display = 'none';
            }
        }

        document.getElementById('wifiForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const select = document.getElementById('ssidSelect');
            const manualInput = document.getElementById('ssidManual');
            const passwordInput = document.getElementById('password');
            const statusBox = document.getElementById('statusBox');
            const submitBtn = document.getElementById('submitBtn');

            let ssid = select.value === '__manual__' ? manualInput.value.trim() : select.value;
            let password = passwordInput.value;

            if (!ssid) {
                alert('Por favor, selecione ou digite o nome da rede Wi-Fi!');
                return;
            }

            const payload = {
                ssid: ssid,
                password: password,
                ip_mode: currentIpMode,
                static_ip: document.getElementById('staticIp').value.trim(),
                gateway: document.getElementById('staticGateway').value.trim(),
                dns: document.getElementById('staticDns').value.trim()
            };

            if (currentIpMode === 'static' && (!payload.static_ip || !payload.gateway)) {
                alert('Por favor, preencha o Endereço IP e o Gateway para o modo IP Fixo!');
                return;
            }

            submitBtn.disabled = true;
            statusBox.className = 'status-box loading';
            statusBox.innerHTML = `<strong>Gravando configuração...</strong><br>Conectando em <em>${ssid}</em>... Aguarde enquanto a impressora obtém o IP.`;

            try {
                const res = await fetch('/api/connect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: json.stringify(payload)
                });
                const data = await res.json();
                
                // Aguardar conexao e checar status
                setTimeout(async () => {
                    await fetchStatus();
                    statusBox.className = 'status-box success';
                    statusBox.innerHTML = `<strong>Configuração Salva!</strong><br>A impressora está aplicando as configurações.<br>Acesse o painel pelo botão abaixo ou por <strong>http://impressora.local</strong>.`;
                    submitBtn.disabled = false;
                }, 5000);
            } catch (err) {
                statusBox.className = 'status-box success';
                statusBox.innerHTML = `<strong>Comando enviado!</strong><br>A impressora está se conectando à nova rede.<br>Acesse pelo seu navegador em <strong>http://impressora.local</strong>.`;
                submitBtn.disabled = false;
            }
        });

        // Inicializacao
        fetchStatus();
        fetchNetworks();
        setInterval(fetchStatus, 8000);
    </script>
</body>
</html>
"""

def get_wifi_status():
    res_conn = subprocess.run(['nmcli', '-t', '-f', 'NAME,DEVICE', 'connection', 'show', '--active'], capture_output=True, text=True)
    active_conn = ''
    for line in res_conn.stdout.splitlines():
        if line.endswith(':wlan0'):
            active_conn = line.split(':')[0]
    
    res_ip = subprocess.run(['ip', '-4', 'addr', 'show', 'dev', 'wlan0'], capture_output=True, text=True)
    ips = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', res_ip.stdout)
    current_ip = ips[0] if ips else ''
    
    res_gw = subprocess.run(['ip', 'route', 'show', 'dev', 'wlan0'], capture_output=True, text=True)
    gws = re.findall(r'default via\s+(\d+\.\d+\.\d+\.\d+)', res_gw.stdout)
    current_gw = gws[0] if gws else ''
    
    res_sig = subprocess.run(['nmcli', '-t', '-f', 'IN-USE,SSID,SIGNAL', 'dev', 'wifi', 'list'], capture_output=True, text=True)
    current_ssid = ''
    current_signal = 0
    for line in res_sig.stdout.splitlines():
        if line.startswith('*:'):
            parts = line.split(':')
            if len(parts) >= 3:
                current_ssid = parts[1]
                try: current_signal = int(parts[2])
                except: current_signal = 100
    
    return {
        "connected": bool(active_conn and active_conn != "Hotspot-Setup"),
        "active_conn": active_conn,
        "ssid": current_ssid or active_conn,
        "ip": current_ip,
        "gateway": current_gw,
        "signal": current_signal,
        "is_hotspot": active_conn == "Hotspot-Setup"
    }

def scan_wifi_networks():
    subprocess.run(['nmcli', 'device', 'wifi', 'rescan'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    res = subprocess.run(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi', 'list'], capture_output=True, text=True)
    networks = []
    seen = set()
    for line in res.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split(':')
        if len(parts) >= 3:
            ssid = parts[0].strip()
            signal = parts[1].strip()
            security = parts[2].strip()
            if ssid and ssid != 'impressora' and ssid != '--' and ssid not in seen:
                seen.add(ssid)
                try:
                    sig_int = int(signal)
                except ValueError:
                    sig_int = 50
                networks.append({"ssid": ssid, "signal": sig_int, "security": security})
    return sorted(networks, key=lambda x: x["signal"], reverse=True)

def apply_wifi_connection(ssid, password, ip_mode="dhcp", static_ip="", gateway="", dns="1.1.1.1, 8.8.8.8"):
    def run_connect():
        time.sleep(1)
        subprocess.run(['nmcli', 'connection', 'delete', 'KlipperOS WiFi'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        cmd_add = [
            'nmcli', 'connection', 'add',
            'type', 'wifi',
            'con-name', 'KlipperOS WiFi',
            'ifname', 'wlan0',
            'ssid', ssid,
            'connection.autoconnect', 'yes',
            'connection.autoconnect-retries', '0'
        ]
        subprocess.run(cmd_add, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if password:
            subprocess.run([
                'nmcli', 'connection', 'modify', 'KlipperOS WiFi',
                '802-11-wireless-security.key-mgmt', 'wpa-psk',
                '802-11-wireless-security.psk', password
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if ip_mode == "static" and static_ip and gateway:
            prefix = "24"
            ip_with_mask = f"{static_ip}/{prefix}" if '/' not in static_ip else static_ip
            subprocess.run([
                'nmcli', 'connection', 'modify', 'KlipperOS WiFi',
                'ipv4.method', 'manual',
                'ipv4.addresses', ip_with_mask,
                'ipv4.gateway', gateway,
                'ipv4.dns', dns or '1.1.1.1,8.8.8.8'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run([
                'nmcli', 'connection', 'modify', 'KlipperOS WiFi',
                'ipv4.method', 'auto'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        subprocess.run(['nmcli', 'connection', 'down', 'Hotspot-Setup'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        subprocess.run(['nmcli', 'connection', 'up', 'KlipperOS WiFi', '--wait', '20'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    t = threading.Thread(target=run_connect)
    t.daemon = True
    t.start()

class PortalHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/status':
            status = get_wifi_status()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode('utf-8'))
            return
            
        if parsed.path == '/api/scan':
            nets = scan_wifi_networks()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(nets).encode('utf-8'))
            return
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_TEMPLATE.encode('utf-8'))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/connect':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                ssid = data.get('ssid', '').strip()
                password = data.get('password', '').strip()
                ip_mode = data.get('ip_mode', 'dhcp')
                static_ip = data.get('static_ip', '').strip()
                gateway = data.get('gateway', '').strip()
                dns = data.get('dns', '').strip()

                if ssid:
                    apply_wifi_connection(ssid, password, ip_mode, static_ip, gateway, dns)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok", "message": "Conectando..."}).encode('utf-8'))
                    return
            except Exception as e:
                pass
            
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "Dados inválidos."}).encode('utf-8'))
            return

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), PortalHandler) as httpd:
        httpd.serve_forever()
