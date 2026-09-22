#!/usr/bin/env python3
import http.server
import socketserver
import json
import subprocess
import urllib.parse
import urllib.request
import ssl
import os
import re
import time
import threading

PORT = 8088

UPDATE_LOCK = threading.Lock()
IS_UPDATING = False
GITHUB_CACHE = {"timestamp": 0, "data": None}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Klipper OS - Central de Controle</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; }
        body { background: #090a0f; color: #f4f4f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px 14px; }
        .card { background: #14151c; border: 1px solid #272730; border-radius: 18px; padding: 28px 24px; width: 100%; max-width: 460px; box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.8); }
        .header { text-align: center; margin-bottom: 18px; }
        .header h1 { font-size: 22px; font-weight: 700; color: #10b981; letter-spacing: -0.5px; margin-bottom: 4px; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .header p { font-size: 13px; color: #a1a1aa; }
        
        .main-tabs { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; background: #0a0b10; padding: 4px; border-radius: 12px; border: 1px solid #272730; margin-bottom: 18px; }
        .main-tab { padding: 9px 4px; text-align: center; font-size: 13px; font-weight: 700; border-radius: 8px; cursor: pointer; color: #a1a1aa; border: none; background: transparent; transition: all 0.2s; white-space: nowrap; }
        .main-tab.active { background: #1c1d26; color: #10b981; border: 1px solid #10b981; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2); }

        .status-panel { background: #1c1d26; border: 1px solid #2e2f3d; border-radius: 12px; padding: 14px; margin-bottom: 18px; font-size: 13px; }
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
        select, input[type="text"], input[type="password"], textarea { width: 100%; padding: 12px 14px; background: #0a0b10; border: 1px solid #333442; border-radius: 10px; color: #ffffff; font-size: 14px; outline: none; transition: border-color 0.2s, box-shadow 0.2s; }
        select:focus, input:focus, textarea:focus { border-color: #10b981; box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2); }
        textarea { font-family: monospace; font-size: 12px; resize: vertical; }

        .file-drop-area { border: 2px dashed #333442; border-radius: 10px; padding: 16px; text-align: center; background: #0a0b10; cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; align-items: center; gap: 6px; }
        .file-drop-area:hover, .file-drop-area.dragover { border-color: #10b981; background: rgba(16, 185, 129, 0.05); }
        .file-icon { font-size: 24px; }
        .file-text { font-size: 13px; color: #a1a1aa; }
        .file-text strong { color: #10b981; }
        
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

        .terminal-box { display: none; background: #050608; color: #34d399; font-family: 'Courier New', Courier, monospace; font-size: 11px; padding: 12px; border-radius: 10px; border: 1px solid #272730; max-height: 200px; overflow-y: auto; margin-top: 14px; white-space: pre-wrap; line-height: 1.4; }

        .footer { text-align: center; margin-top: 22px; font-size: 12px; color: #71717a; }
        .footer a { color: #10b981; text-decoration: none; }
        .password-container { position: relative; }
        .toggle-pw { position: absolute; right: 12px; top: 12px; background: none; border: none; color: #a1a1aa; cursor: pointer; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1 id="mainTitle">🖨️ Klipper OS Wi-Fi</h1>
            <p id="mainSubtitle">Gerenciamento de Rede e Recursos da Impressora</p>
        </div>

        <!-- Abas Principais -->
        <div class="main-tabs">
            <button type="button" class="main-tab active" id="tabNavWifi" onclick="switchTab('wifi')">📶 Wi-Fi</button>
            <button type="button" class="main-tab" id="tabNavCreality" onclick="switchTab('creality')">☁️ Creality</button>
            <button type="button" class="main-tab" id="tabNavUpdate" onclick="switchTab('update')">🔄 Sistema</button>
        </div>

        <!-- SECAO 1: WI-FI -->
        <div id="sectionWifi">
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

                <div class="form-group">
                    <label for="password">Senha da Rede</label>
                    <div class="password-container">
                        <input type="password" id="password" placeholder="Digite a senha do Wi-Fi..." autocomplete="current-password">
                        <button type="button" class="toggle-pw" onclick="togglePassword()">👁️</button>
                    </div>
                </div>

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

            <a id="mainsailLink" href="/" class="btn-secondary">
                🚀 Abrir Painel Mainsail
            </a>
        </div>

        <!-- SECAO 2: CREALITY CLOUD -->
        <div id="sectionCreality" style="display: none;">
            <div class="status-panel">
                <div class="status-row">
                    <span class="status-label">Serviço de Nuvem:</span>
                    <span class="status-val" id="ccServiceStatus"><span class="badge-yellow">Verificando...</span></span>
                </div>
                <div class="status-row">
                    <span class="status-label">Conexão Creality Cloud:</span>
                    <span class="status-val" id="ccCloudStatus"><span class="badge-yellow">Verificando...</span></span>
                </div>
                <div class="status-row">
                    <span class="status-label">Modelo Vinculado:</span>
                    <span class="status-val" id="ccModel">--</span>
                </div>
                <div class="status-row">
                    <span class="status-label">Dispositivo ID:</span>
                    <span class="status-val" id="ccDeviceId" style="font-family: monospace; font-size: 12px;">--</span>
                </div>
            </div>

            <form id="crealityForm">
                <div class="form-group">
                    <label>1. Arquivo de Credencial (.tk)</label>
                    <div class="file-drop-area" id="dropArea" onclick="document.getElementById('tkFileInput').click()">
                        <span class="file-icon">📁</span>
                        <span class="file-text" id="fileText">Clique para carregar <strong>rasp_pie_credential.tk</strong></span>
                        <input type="file" id="tkFileInput" accept=".tk,.json,.txt" style="display: none;" onchange="handleFileSelect(event)">
                    </div>
                </div>

                <div class="form-group">
                    <label for="tkText">Ou Cole o Token / JSON do Arquivo:</label>
                    <textarea id="tkText" rows="3" placeholder="Cole aqui o token eyJhbGci... ou o conteúdo do arquivo .tk"></textarea>
                </div>

                <div class="form-group">
                    <label for="crealityModel">2. Modelo da Impressora 3D</label>
                    <select id="crealityModel" onchange="handleModelChange()">
                        <option value="Ender-3 V3 SE" selected>Ender-3 V3 SE</option>
                        <option value="Ender-3 V3 KE">Ender-3 V3 KE</option>
                        <option value="Ender-3 V3">Ender-3 V3</option>
                        <option value="Ender-3 S1">Ender-3 S1</option>
                        <option value="Ender-3 S1 Pro">Ender-3 S1 Pro</option>
                        <option value="Ender-3 V2 Neo">Ender-3 V2 Neo</option>
                        <option value="Ender-3 V2">Ender-3 V2</option>
                        <option value="Ender-3 Max Neo">Ender-3 Max Neo</option>
                        <option value="Ender-3 Neo">Ender-3 Neo</option>
                        <option value="Ender-3 Pro">Ender-3 Pro</option>
                        <option value="Ender-3">Ender-3</option>
                        <option value="CR-10 Smart">CR-10 Smart</option>
                        <option value="CR-10 Smart Pro">CR-10 Smart Pro</option>
                        <option value="CR-6 SE">CR-6 SE</option>
                        <option value="K1">K1</option>
                        <option value="K1 Max">K1 Max</option>
                        <option value="__custom__">➕ Outro Modelo (Digitar)...</option>
                    </select>
                    <input type="text" id="crealityModelCustom" placeholder="Digite o modelo exato..." style="display: none; margin-top: 8px;">
                </div>

                <button type="submit" class="btn-green" id="ccSubmitBtn">☁️ Vincular e Ativar Creality Cloud</button>
            </form>

            <div id="ccStatusBox" class="status-box"></div>

            <div style="display: flex; gap: 8px; margin-top: 10px;">
                <button type="button" class="btn-secondary" style="flex: 1; margin-top: 0;" onclick="restartCrealityService()">🔄 Reiniciar Nuvem</button>
                <button type="button" class="btn-secondary" style="flex: 1; margin-top: 0; color: #f87171;" onclick="resetCrealityConfig()">🗑️ Desvincular</button>
            </div>
        </div>

        <!-- SECAO 3: ATUALIZACAO DO SISTEMA -->
        <div id="sectionUpdate" style="display: none;">
            <div class="status-panel">
                <div class="status-row">
                    <span class="status-label">Versão Instalada:</span>
                    <span class="status-val" id="curLocalCommit">--</span>
                </div>
                <div class="status-row">
                    <span class="status-label">Último no GitHub:</span>
                    <span class="status-val" id="curRemoteCommit">--</span>
                </div>
                <div class="status-row">
                    <span class="status-label">Status do Sistema:</span>
                    <span class="status-val" id="updateBadge"><span class="badge-yellow">Verificando...</span></span>
                </div>
                <div class="status-row" style="flex-direction: column; align-items: flex-start; gap: 4px; margin-top: 8px;">
                    <span class="status-label">Última Modificação:</span>
                    <span id="curCommitMsg" style="font-size: 12px; color: #a1a1aa; font-style: italic; word-break: break-word;">--</span>
                </div>
            </div>

            <button type="button" class="btn-green" id="btnDoUpdate" onclick="startSystemUpdate()">🚀 Atualizar Sistema Agora (1-Clique)</button>
            <button type="button" class="btn-secondary" id="btnCheckUpdate" onclick="fetchUpdateStatus(true)">🔄 Verificar Atualizações</button>

            <div id="updateStatusBox" class="status-box"></div>
            <div id="updateLogBox" class="terminal-box"></div>
        </div>

        <div class="footer">
            Klipper OS RK322x • <a href="http://impressora.local">impressora.local</a>
        </div>
    </div>

    <script>
        let currentIpMode = 'dhcp';
        let activeTab = 'wifi';
        let isUpdating = false;
        let updatePollInterval = null;

        function switchTab(tab) {
            activeTab = tab;
            document.getElementById('tabNavWifi').className = tab === 'wifi' ? 'main-tab active' : 'main-tab';
            document.getElementById('tabNavCreality').className = tab === 'creality' ? 'main-tab active' : 'main-tab';
            document.getElementById('tabNavUpdate').className = tab === 'update' ? 'main-tab active' : 'main-tab';
            
            document.getElementById('sectionWifi').style.display = tab === 'wifi' ? 'block' : 'none';
            document.getElementById('sectionCreality').style.display = tab === 'creality' ? 'block' : 'none';
            document.getElementById('sectionUpdate').style.display = tab === 'update' ? 'block' : 'none';
            
            const title = document.getElementById('mainTitle');
            const subtitle = document.getElementById('mainSubtitle');
            if (tab === 'wifi') {
                title.innerHTML = '🖨️ Klipper OS Wi-Fi';
                subtitle.textContent = 'Gerenciamento de Rede da Impressora';
                fetchStatus();
            } else if (tab === 'creality') {
                title.innerHTML = '☁️ Creality Cloud';
                subtitle.textContent = 'Vincule sua impressora ao app móvel Creality';
                fetchCrealityStatus();
            } else {
                title.innerHTML = '🔄 Atualização OTA';
                subtitle.textContent = 'Mantenha seu Klipper OS atualizado com 1 clique';
                fetchUpdateStatus();
            }
        }

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

        function handleModelChange() {
            const select = document.getElementById('crealityModel');
            const custom = document.getElementById('crealityModelCustom');
            if (select.value === '__custom__') {
                custom.style.display = 'block';
                custom.focus();
            } else {
                custom.style.display = 'none';
            }
        }

        function handleFileSelect(e) {
            const file = e.target.files[0];
            if (!file) return;
            const fileText = document.getElementById('fileText');
            fileText.innerHTML = `Arquivo: <strong>${file.name}</strong> (${(file.size/1024).toFixed(1)} KB)`;
            
            const reader = new FileReader();
            reader.onload = function(evt) {
                document.getElementById('tkText').value = evt.target.result.trim();
            };
            reader.readAsText(file);
        }

        // Drag and drop support
        const dropArea = document.getElementById('dropArea');
        if (dropArea) {
            ['dragenter', 'dragover'].forEach(eventName => {
                dropArea.addEventListener(eventName, (e) => { e.preventDefault(); dropArea.classList.add('dragover'); }, false);
            });
            ['dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, (e) => { e.preventDefault(); dropArea.classList.remove('dragover'); }, false);
            });
            dropArea.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                const files = dt.files;
                if (files.length) {
                    document.getElementById('tkFileInput').files = files;
                    handleFileSelect({ target: { files: files } });
                }
            });
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

        async function fetchCrealityStatus() {
            try {
                const res = await fetch('/api/creality/status');
                const data = await res.json();
                const sService = document.getElementById('ccServiceStatus');
                const sCloud = document.getElementById('ccCloudStatus');
                const sModel = document.getElementById('ccModel');
                const sDevice = document.getElementById('ccDeviceId');

                if (data.service_active) {
                    sService.innerHTML = '<span class="badge-green">🟢 Ativo</span>';
                } else {
                    sService.innerHTML = '<span class="badge-red">🔴 Parado</span>';
                }

                if (data.connected) {
                    sCloud.innerHTML = '<span class="badge-green">🟢 Conectado à Nuvem</span>';
                } else if (data.configured) {
                    sCloud.innerHTML = '<span class="badge-yellow">🟡 Configurado (Conectando...)</span>';
                } else {
                    sCloud.innerHTML = '<span class="badge-yellow">⚪ Não Configurado</span>';
                }

                sModel.textContent = data.model || '--';
                sDevice.textContent = data.device_name || 'Nenhum';

                if (data.model && data.model !== '--') {
                    const select = document.getElementById('crealityModel');
                    let found = false;
                    for (let opt of select.options) {
                        if (opt.value === data.model) {
                            select.value = data.model;
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        select.value = '__custom__';
                        document.getElementById('crealityModelCustom').style.display = 'block';
                        document.getElementById('crealityModelCustom').value = data.model;
                    }
                }
            } catch (e) {
                console.error('Creality status fetch error:', e);
            }
        }

        async function fetchUpdateStatus(force) {
            const btnCheck = document.getElementById('btnCheckUpdate');
            if (btnCheck) { btnCheck.disabled = true; btnCheck.textContent = 'Consultando GitHub...'; }

            try {
                const res = await fetch('/api/update/status' + (force ? '?force=1' : ''));
                const data = await res.json();

                document.getElementById('curLocalCommit').innerHTML = `<code>${data.local_sha}</code>`;
                document.getElementById('curRemoteCommit').innerHTML = `<a href="https://github.com/ratfumace/Klipper-OS-RK322x-R329Q-SSV6051/commit/${data.remote_sha_full}" target="_blank" style="color: #10b981;"><code>${data.remote_sha}</code> ↗</a>`;
                document.getElementById('curCommitMsg').textContent = data.remote_msg || 'Sem detalhes';

                const badge = document.getElementById('updateBadge');
                const btnUpdate = document.getElementById('btnDoUpdate');

                if (data.is_updating) {
                    badge.innerHTML = '<span class="badge-yellow">⏳ Atualização em Andamento</span>';
                    btnUpdate.disabled = true;
                    btnUpdate.textContent = '⏳ Atualizando o sistema...';
                    startLogPolling();
                } else if (data.update_available) {
                    badge.innerHTML = '<span class="badge-yellow">🚀 Nova Atualização Disponível!</span>';
                    btnUpdate.disabled = false;
                    btnUpdate.textContent = '🚀 Atualizar Sistema Agora (1-Clique)';
                    btnUpdate.className = 'btn-green';
                } else {
                    badge.innerHTML = '<span class="badge-green">🟢 Sistema Atualizado</span>';
                    btnUpdate.disabled = false;
                    btnUpdate.textContent = '🛠️ Reinstalar / Reparar Versão Mais Recente';
                    btnUpdate.className = 'btn-secondary';
                }
            } catch (e) {
                console.error('Update status fetch error:', e);
            } finally {
                if (btnCheck) { btnCheck.disabled = false; btnCheck.textContent = '🔄 Verificar Atualizações'; }
            }
        }

        async function startSystemUpdate() {
            if (!confirm('Deseja iniciar a atualização do sistema? O portal e os scripts serão atualizados diretamente a partir do GitHub.')) return;
            
            const btn = document.getElementById('btnDoUpdate');
            const statusBox = document.getElementById('updateStatusBox');
            const logBox = document.getElementById('updateLogBox');

            btn.disabled = true;
            btn.textContent = '⏳ Baixando e aplicando atualização...';
            statusBox.className = 'status-box loading';
            statusBox.innerHTML = '<strong>Iniciando atualização...</strong><br>Conectando ao GitHub e baixando novas versões...';
            logBox.style.display = 'block';
            logBox.textContent = 'Iniciando atualização do Klipper OS...';

            try {
                const res = await fetch('/api/update/start', { method: 'POST' });
                const data = await res.json();
                startLogPolling();
            } catch (err) {
                statusBox.className = 'status-box error';
                statusBox.innerHTML = `<strong>Erro ao iniciar atualização:</strong> ${err.message}`;
                btn.disabled = false;
            }
        }

        function startLogPolling() {
            if (updatePollInterval) clearInterval(updatePollInterval);
            
            const statusBox = document.getElementById('updateStatusBox');
            const logBox = document.getElementById('updateLogBox');
            const btn = document.getElementById('btnDoUpdate');

            updatePollInterval = setInterval(async () => {
                try {
                    const res = await fetch('/api/update/log');
                    const data = await res.json();
                    
                    if (data.log) {
                        logBox.style.display = 'block';
                        logBox.textContent = data.log;
                        logBox.scrollTop = logBox.scrollHeight;
                    }

                    if (data.success) {
                        clearInterval(updatePollInterval);
                        statusBox.className = 'status-box success';
                        statusBox.innerHTML = '<strong>🎉 Atualização Concluída com Sucesso!</strong><br>O portal foi atualizado e reiniciado.<br>Recarregando em instantes...';
                        btn.textContent = '✅ Atualização Concluída';
                        setTimeout(() => window.location.reload(), 4500);
                    } else if (data.error && !data.running) {
                        clearInterval(updatePollInterval);
                        statusBox.className = 'status-box error';
                        statusBox.innerHTML = '<strong>Ocorreu um erro durante a atualização.</strong><br>Consulte o log acima para detalhes.';
                        btn.disabled = false;
                        btn.textContent = 'Tentar Novamente';
                    }
                } catch (e) {
                    // Servidor pode estar reiniciando
                }
            }, 1000);
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
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
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

        // Submissao Creality Cloud
        document.getElementById('crealityForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const tkText = document.getElementById('tkText').value.trim();
            const modelSelect = document.getElementById('crealityModel');
            const modelCustom = document.getElementById('crealityModelCustom');
            const statusBox = document.getElementById('ccStatusBox');
            const submitBtn = document.getElementById('ccSubmitBtn');

            if (!tkText) {
                alert('Por favor, selecione o arquivo rasp_pie_credential.tk ou cole o conteúdo do token!');
                return;
            }

            let model = modelSelect.value === '__custom__' ? modelCustom.value.trim() : modelSelect.value;
            if (!model) {
                model = 'Ender-3 V3 SE';
            }

            submitBtn.disabled = true;
            statusBox.className = 'status-box loading';
            statusBox.innerHTML = '<strong>Comunicando com a Creality Cloud...</strong><br>Autenticando token e registrando dispositivo na nuvem...';

            try {
                const res = await fetch('/api/creality/setup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: tkText, model: model })
                });
                const data = await res.json();

                if (data.status === 'ok') {
                    statusBox.className = 'status-box success';
                    statusBox.innerHTML = `<strong>Sucesso!</strong><br>${data.message}<br>ID do Dispositivo: <code>${data.device_name}</code><br>Abra o app <strong>Creality Cloud</strong> no celular para confirmar a conexão!`;
                    setTimeout(fetchCrealityStatus, 3000);
                } else {
                    statusBox.className = 'status-box error';
                    statusBox.innerHTML = `<strong>Falha na Configuração:</strong><br>${data.message || 'Erro desconhecido'}`;
                }
            } catch (err) {
                statusBox.className = 'status-box error';
                statusBox.innerHTML = `<strong>Erro de Comunicação:</strong><br>${err.message}`;
            } finally {
                submitBtn.disabled = false;
            }
        });

        async function restartCrealityService() {
            const statusBox = document.getElementById('ccStatusBox');
            statusBox.className = 'status-box loading';
            statusBox.innerHTML = '<strong>Reiniciando serviço Creality Cloud...</strong>';
            try {
                const res = await fetch('/api/creality/restart', { method: 'POST' });
                const data = await res.json();
                statusBox.className = 'status-box success';
                statusBox.innerHTML = `<strong>${data.message}</strong>`;
                setTimeout(fetchCrealityStatus, 4000);
            } catch (err) {
                statusBox.className = 'status-box error';
                statusBox.innerHTML = `<strong>Erro ao reiniciar:</strong> ${err.message}`;
            }
        }

        async function resetCrealityConfig() {
            if (!confirm('Tem certeza que deseja desvincular a Creality Cloud desta impressora?')) return;
            const statusBox = document.getElementById('ccStatusBox');
            statusBox.className = 'status-box loading';
            statusBox.innerHTML = '<strong>Removendo credenciais...</strong>';
            try {
                const res = await fetch('/api/creality/reset', { method: 'POST' });
                const data = await res.json();
                statusBox.className = 'status-box success';
                statusBox.innerHTML = `<strong>${data.message}</strong>`;
                document.getElementById('tkText').value = '';
                document.getElementById('fileText').innerHTML = 'Clique para carregar <strong>rasp_pie_credential.tk</strong>';
                setTimeout(fetchCrealityStatus, 2000);
            } catch (err) {
                statusBox.className = 'status-box error';
                statusBox.innerHTML = `<strong>Erro ao desvincular:</strong> ${err.message}`;
            }
        }

        // Inicializacao
        fetchStatus();
        fetchNetworks();
        fetchCrealityStatus();
        fetchUpdateStatus();
        setInterval(() => {
            if (activeTab === 'wifi') fetchStatus();
            else if (activeTab === 'creality') fetchCrealityStatus();
            else if (activeTab === 'update' && !isUpdating) fetchUpdateStatus();
        }, 8000);
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

# Funcoes Creality Cloud
def get_device_mac():
    for iface in ['wlan0', 'eth0']:
        path = f'/sys/class/net/{iface}/address'
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    mac = f.read().strip()
                    if mac and mac != '00:00:00:00:00:00':
                        return mac
            except Exception:
                pass
    import uuid
    mac_num = uuid.getnode()
    return ':'.join(re.findall('..', '%012x' % mac_num))

def extract_jwt_token(raw_input):
    if not raw_input:
        return None
    raw_input = raw_input.strip()
    try:
        data = json.loads(raw_input)
        if isinstance(data, dict):
            if 'token' in data:
                return data['token'].strip()
            if 'app_token' in data:
                return data['app_token'].strip()
    except Exception:
        pass
    
    match = re.search(r'eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+', raw_input)
    if match:
        return match.group(0)
    
    if len(raw_input) > 50 and '.' in raw_input:
        return raw_input
    return None

def ensure_octoprint_sd_disabled():
    try:
        octo_cfg = '/home/klipper/.octoprint/config.yaml'
        if os.path.exists(octo_cfg):
            import yaml
            with open(octo_cfg, 'r') as f:
                data = yaml.safe_load(f) or {}
            if 'feature' not in data:
                data['feature'] = {}
            if data['feature'].get('sdSupport') is not False:
                data['feature']['sdSupport'] = False
                with open(octo_cfg, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False)
    except Exception:
        pass

def get_creality_status():
    octo_installed = os.path.exists('/home/klipper/OctoPrint/venv/bin/octoprint')
    service_active = False
    try:
        res = subprocess.run(['systemctl', 'is-active', 'octoprint.service'], capture_output=True, text=True)
        service_active = (res.stdout.strip() == 'active')
    except Exception:
        pass
    
    cfg_path = '/home/klipper/.octoprint/data/crealitycloud/config.json'
    configured = False
    device_name = ''
    model = 'Ender-3 V3 SE'
    region = 5
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, 'r') as f:
                cfg = json.load(f)
                device_name = cfg.get('deviceName', '')
                model = cfg.get('model', 'Ender-3 V3 SE')
                region = cfg.get('region', 5)
                configured = bool(device_name)
        except Exception:
            pass
            
    mqtt_connected = False
    if service_active:
        try:
            res_ss = subprocess.run(['ss', '-tnp', '( dport = :1883 )'], capture_output=True, text=True)
            if 'ESTAB' in res_ss.stdout and 'octoprint' in res_ss.stdout:
                mqtt_connected = True
        except Exception:
            pass
            
    return {
        "installed": octo_installed,
        "service_active": service_active,
        "configured": configured,
        "device_name": device_name,
        "model": model,
        "region": region,
        "connected": mqtt_connected
    }

def setup_creality_cloud(token_raw, model="Ender-3 V3 SE"):
    token = extract_jwt_token(token_raw)
    if not token:
        return {"status": "error", "message": "Token inválido. Envie o arquivo rasp_pie_credential.tk ou cole o JWT."}
        
    mac = get_device_mac()
    url = "https://api.crealitycloud.com/api/cxy/v2/device/user/importDevice"
    headers = {
        "__CXY_JWTOKEN_": token,
        "Content-Type": "application/json",
        "User-Agent": "CrealityCloud/1.0"
    }
    payload = json.dumps({"mac": mac, "iotType": 2}).encode('utf-8')
    
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            resp_body = resp.read().decode('utf-8')
            resp_data = json.loads(resp_body)
    except Exception as e:
        return {"status": "error", "message": f"Erro de conexão com Creality Cloud: {str(e)}"}
        
    code = resp_data.get("code")
    if code != 0:
        msg = resp_data.get("msg", "Falha na autenticação")
        return {"status": "error", "message": f"Creality Cloud rejeitou o token (código {code}): {msg}"}
        
    result = resp_data.get("result", {})
    device_name = result.get("deviceName")
    device_secret = result.get("tbToken")
    region_id = result.get("regionId", 5)
    
    if not device_name or not device_secret:
        return {"status": "error", "message": f"Resposta incompleta da Creality Cloud: {resp_body}"}
        
    cfg_dir = '/home/klipper/.octoprint/data/crealitycloud'
    os.makedirs(cfg_dir, exist_ok=True)
    cfg_path = os.path.join(cfg_dir, 'config.json')
    
    config_content = {
        "deviceName": device_name,
        "deviceSecret": device_secret,
        "iotType": 2,
        "region": region_id,
        "model": model,
        "token": token
    }
    
    with open(cfg_path, 'w') as f:
        json.dump(config_content, f, indent=2)
        
    ensure_octoprint_sd_disabled()
    subprocess.run(['chown', '-R', 'klipper:klipper', '/home/klipper/.octoprint'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['systemctl', 'restart', 'octoprint.service'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return {
        "status": "ok",
        "message": f"Impressora vinculada com sucesso à Creality Cloud!",
        "device_name": device_name,
        "model": model
    }

# Funcoes de Atualizacao do Sistema
def get_local_version():
    v_path = "/etc/klipper-os-version.json"
    if os.path.exists(v_path):
        try:
            with open(v_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "commit_sha": "pre-commit",
        "commit_date": "--",
        "commit_message": "Versão Base Klipper OS"
    }

def get_remote_version(force=False):
    now = time.time()
    if not force and GITHUB_CACHE["data"] and (now - GITHUB_CACHE["timestamp"]) < 45:
        return GITHUB_CACHE["data"]
        
    url = "https://api.github.com/repos/ratfumace/Klipper-OS-RK322x-R329Q-SSV6051/commits/main"
    headers = {"User-Agent": "KlipperOS-Updater/1.0"}
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            sha = data.get("sha", "")
            date = data.get("commit", {}).get("author", {}).get("date", "")
            msg = data.get("commit", {}).get("message", "").splitlines()[0]
            result = {"sha": sha, "date": date, "msg": msg}
            GITHUB_CACHE["timestamp"] = now
            GITHUB_CACHE["data"] = result
            return result
    except Exception as e:
        if GITHUB_CACHE["data"]:
            return GITHUB_CACHE["data"]
        return {"sha": "unknown", "date": "", "msg": f"Erro de conexão: {str(e)}"}

def run_system_update():
    global IS_UPDATING
    with UPDATE_LOCK:
        IS_UPDATING = True
        try:
            updater_script = "/usr/local/bin/klipper_os_updater.sh"
            if not os.path.exists(updater_script):
                url = "https://raw.githubusercontent.com/ratfumace/Klipper-OS-RK322x-R329Q-SSV6051/main/tudo_que_foi_usado/06_klipper_os_updater.sh"
                urllib.request.urlretrieve(url, updater_script)
                os.chmod(updater_script, 0o755)
            
            subprocess.run(["/bin/bash", updater_script])
        except Exception as e:
            with open("/var/log/klipper_os_update.log", "a") as f:
                f.write(f"\nERRO EXCEÇÃO: {str(e)}\n")
        finally:
            IS_UPDATING = False

class PortalHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.do_GET()

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

        if parsed.path == '/api/creality/status':
            cc_status = get_creality_status()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(cc_status).encode('utf-8'))
            return

        if parsed.path == '/api/update/status':
            query = urllib.parse.parse_qs(parsed.query)
            force = 'force' in query
            local_info = get_local_version()
            remote_info = get_remote_version(force=force)
            
            local_sha = local_info.get("commit_sha", "pre-commit")
            remote_sha = remote_info.get("sha", "")
            
            update_available = (remote_sha and remote_sha != "unknown" and local_sha[:7] != remote_sha[:7])
            
            resp_payload = {
                "local_sha": local_sha[:7] if local_sha != "pre-commit" else "Pré-commit",
                "remote_sha": remote_sha[:7] if remote_sha != "unknown" else "Desconhecido",
                "remote_sha_full": remote_sha,
                "remote_date": remote_info.get("date", ""),
                "remote_msg": remote_info.get("msg", ""),
                "update_available": update_available,
                "is_updating": IS_UPDATING
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload).encode('utf-8'))
            return

        if parsed.path == '/api/update/log':
            log_path = "/var/log/klipper_os_update.log"
            content = ""
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r") as f:
                        lines = f.readlines()
                        content = "".join(lines[-70:])
                except Exception as e:
                    content = f"Erro ao ler log: {str(e)}"
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "running": IS_UPDATING,
                "log": content,
                "success": "STATUS: SUCCESS" in content,
                "error": "ERRO:" in content
            }).encode('utf-8'))
            return
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_TEMPLATE.encode('utf-8'))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        if parsed.path == '/api/connect':
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
            except Exception:
                pass
            
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "Dados inválidos."}).encode('utf-8'))
            return

        if parsed.path == '/api/creality/setup':
            try:
                data = json.loads(post_data.decode('utf-8'))
                token = data.get('token', '')
                model = data.get('model', 'Ender-3 V3 SE').strip() or 'Ender-3 V3 SE'
                result = setup_creality_cloud(token, model)
                self.send_response(200 if result.get("status") == "ok" else 400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                return

        if parsed.path == '/api/creality/restart':
            ensure_octoprint_sd_disabled()
            subprocess.run(['systemctl', 'restart', 'octoprint.service'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Serviço Creality Cloud reiniciado!"}).encode('utf-8'))
            return

        if parsed.path == '/api/creality/reset':
            cfg_path = '/home/klipper/.octoprint/data/crealitycloud/config.json'
            if os.path.exists(cfg_path):
                try:
                    os.remove(cfg_path)
                except Exception:
                    pass
            subprocess.run(['systemctl', 'restart', 'octoprint.service'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Configurações da Creality Cloud removidas com sucesso!"}).encode('utf-8'))
            return

        if parsed.path == '/api/update/start':
            if IS_UPDATING:
                self.send_response(409)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Atualização já em andamento."}).encode('utf-8'))
                return
                
            t = threading.Thread(target=run_system_update)
            t.daemon = True
            t.start()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Processo de atualização iniciado com sucesso!"}).encode('utf-8'))
            return

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), PortalHandler) as httpd:
        httpd.serve_forever()
