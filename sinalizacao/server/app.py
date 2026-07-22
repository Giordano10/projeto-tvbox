from __future__ import annotations

from functools import wraps

from flask import Flask, abort, jsonify, render_template_string, request, send_file, session

from .service import SignalizacaoService


service = SignalizacaoService()


PANEL_HTML = """<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Painel TV Box • Sinalização Digital</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090d16;
            --panel: rgba(15, 23, 42, 0.85);
            --panel-border: rgba(255, 255, 255, 0.1);
            --text: #f8fafc;
            --muted: #94a3b8;
            --accent: #14b8a6;
            --accent-gradient: linear-gradient(135deg, #0d9488, #2563eb);
            --accent-hover: linear-gradient(135deg, #14b8a6, #3b82f6);
            --danger: #ef4444;
            --danger-gradient: linear-gradient(135deg, #dc2626, #b91c1c);
            --card-bg: rgba(30, 41, 59, 0.7);
            --input-bg: #0f172a;
            --success: #22c55e;
            --warning: #f59e0b;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: radial-gradient(ellipse at top, #1e293b 0%, #0f172a 50%, #090d16 100%);
            color: var(--text);
            min-height: 100vh;
        }
        header {
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--panel-border);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .header-content {
            max-width: 1280px;
            margin: 0 auto;
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo-box { display: flex; align-items: center; gap: 12px; }
        .logo-icon {
            width: 40px;
            height: 40px;
            border-radius: 12px;
            background: var(--accent-gradient);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 20px;
            color: #fff;
            box-shadow: 0 4px 16px rgba(13, 148, 136, 0.3);
        }
        .logo-title { margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.5px; }
        .logo-sub { font-size: 12px; color: var(--muted); margin: 0; }
        
        .nav-tabs {
            max-width: 1280px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            gap: 8px;
            border-bottom: 1px solid var(--panel-border);
        }
        .tab-btn {
            background: transparent;
            border: none;
            color: var(--muted);
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
        }
        .tab-btn:hover { color: var(--text); }
        .tab-btn.active {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }

        main { max-width: 1280px; margin: 0 auto; padding: 24px; }
        .tab-content { display: none; }
        .tab-content.active { display: block; animation: fadeIn 0.3s ease; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.3);
        }
        .card-title {
            margin: 0 0 16px 0;
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        label { display: block; font-size: 13px; font-weight: 500; color: var(--muted); margin-bottom: 6px; }
        input, select, textarea {
            width: 100%;
            background: var(--input-bg);
            border: 1px solid var(--panel-border);
            border-radius: 10px;
            color: var(--text);
            padding: 12px 14px;
            font-size: 14px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }
        input:focus, select:focus, textarea:focus { border-color: var(--accent); }

        button {
            width: 100%;
            padding: 12px 18px;
            border-radius: 10px;
            border: none;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            background: var(--accent-gradient);
            color: #fff;
            transition: transform 0.1s, opacity 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        button:hover { opacity: 0.95; }
        button:active { transform: scale(0.98); }
        button.secondary { background: rgba(51, 65, 85, 0.8); color: var(--text); border: 1px solid var(--panel-border); }
        button.danger { background: var(--danger-gradient); }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-online { background: rgba(34, 197, 94, 0.15); color: var(--success); }
        .badge-offline { background: rgba(239, 68, 68, 0.15); color: var(--danger); }

        .device-card {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--panel-border);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
        }

        .chat-box {
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid var(--panel-border);
            border-radius: 12px;
            height: 320px;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 12px;
        }
        .chat-msg {
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.4;
        }
        .chat-msg.user { background: #2563eb; color: #fff; align-self: flex-end; border-bottom-right-radius: 2px; }
        .chat-msg.bot { background: #334155; color: var(--text); align-self: flex-start; border-bottom-left-radius: 2px; }
        .chat-msg.system { background: rgba(13, 148, 136, 0.2); color: var(--accent); align-self: center; font-size: 12px; border-radius: 20px; }

        .media-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; margin-top: 12px; }
        .media-item {
            background: #0f172a;
            border: 1px solid var(--panel-border);
            border-radius: 10px;
            padding: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .media-item:hover { border-color: var(--accent); transform: translateY(-2px); }
        .media-item img { width: 100%; height: 90px; object-fit: cover; border-radius: 6px; }
        .media-item span { display: block; font-size: 11px; color: var(--muted); margin-top: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

        .log-list { max-height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px; background: #0f172a; padding: 12px; border-radius: 10px; border: 1px solid var(--panel-border); }
        .log-entry { margin-bottom: 6px; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.05); }

        @media (max-width: 768px) { .grid-2 { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <div class="logo-box">
                <div class="logo-icon">TV</div>
                <div>
                    <h1 class="logo-title">Gestor PicoClaw TV Box</h1>
                    <p class="logo-sub">Sinalização Digital Local-First</p>
                </div>
            </div>
            <div id="authStatus" style="display: flex; align-items: center; gap: 16px;">
                <span style="font-size: 14px; color: var(--muted);">👤 Logado como: <strong style="color: var(--text);">{{ username }}</strong></span>
                <a href="/logout" style="color: var(--danger); text-decoration: none; font-size: 13px; font-weight: 500;">Sair</a>
            </div>
        </div>
        <nav class="nav-tabs">
            <button class="tab-btn active" onclick="switchTab('telas')">📺 Controle de Telas</button>
            <button class="tab-btn" onclick="switchTab('cartazes')">🎨 Gerador de Cartazes</button>
            <button class="tab-btn" onclick="switchTab('picoclaw')">💬 Chat Interativo</button>
            <button class="tab-btn" onclick="switchTab('dispositivos')">📡 Dispositivos & IPs</button>
            <button class="tab-btn" onclick="switchTab('auditoria')">📋 Auditoria & Permissões</button>
        </nav>
    </header>

    <main>
        <!-- ABA 1: CONTROLE DE TELAS -->
        <div id="tab-telas" class="tab-content active">
            <div class="grid-2">
                <div class="card">
                    <h3 class="card-title">Publicar Conteúdo em Tela</h3>
                    <div style="display: grid; gap: 12px;">
                        <div>
                            <label for="selectTela">Selecione a TV de Destino</label>
                            <select id="selectTela"></select>
                        </div>
                        <div>
                            <label for="inputMidia">Caminho da Mídia</label>
                            <input id="inputMidia" placeholder="biblioteca/avisos.png" value="biblioteca/avisos.png">
                        </div>
                        <div class="grid-2">
                            <button onclick="exibirMidia()">Exibir Mídia</button>
                            <button class="danger" onclick="limparTela()">Limpar Tela</button>
                        </div>
                        <button class="secondary" onclick="rotacionarTela()">Alternar Playlist/Rotação</button>
                    </div>
                </div>

                <div class="card">
                    <h3 class="card-title">Galeria da Biblioteca</h3>
                    <div id="mediaGallery" class="media-grid"></div>
                </div>
            </div>
        </div>

        <!-- ABA 2: GERADOR DE CARTAZES -->
        <div id="tab-cartazes" class="tab-content">
            <div class="card" style="max-width: 650px; margin: 0 auto;">
                <h3 class="card-title">Gerar Cartaz / Slide em HD</h3>
                <div style="display: grid; gap: 16px;">
                    <div>
                        <label for="slideTela">TV de Destino</label>
                        <select id="slideTela"></select>
                    </div>
                    <div>
                        <label for="slideTitulo">Título do Cartaz</label>
                        <input id="slideTitulo" placeholder="Ex: Reunião de Pais e Mestres" value="Aviso Importante">
                    </div>
                    <div>
                        <label for="slideCorpo">Corpo da Mensagem</label>
                        <textarea id="slideCorpo" placeholder="Escreva o texto do comunicado que aparecerá na TV...">Informamos que haverá reunião geral nesta sexta-feira às 19h no auditório principal.</textarea>
                    </div>
                    <button onclick="gerarSlide()">🎨 Gerar e Publicar Cartaz</button>
                </div>
            </div>
        </div>

        <!-- ABA 3: CHAT INTERATIVO -->
        <div id="tab-picoclaw" class="tab-content">
            <div class="card" style="max-width: 700px; margin: 0 auto;">
                <h3 class="card-title">Assistente em Linguagem Natural</h3>
                <p style="font-size: 13px; color: var(--muted); margin-top: -8px;">Envie instruções em linguagem natural ou adicione mídias para as telas (ex: "coloca o aviso da reuniao na tv_saguao").</p>
                
                <div id="chatHistory" class="chat-box">
                    <div class="chat-msg system">Assistente pronto para comandos.</div>
                </div>

                <div style="display: flex; gap: 10px; align-items: center;">
                    <label for="chatAnexo" style="cursor: pointer; padding: 10px; background: var(--input-bg); border-radius: 6px; border: 1px solid var(--panel-border);" title="Anexar Imagem">📎</label>
                    <input type="file" id="chatAnexo" accept="image/*,video/*" style="display: none;" onchange="updateAnexoLabel(this)">
                    <input id="inputChat" style="flex: 1;" placeholder="Digite uma instrução em linguagem natural..." onkeypress="if(event.key==='Enter') enviarComandoChat()">
                    <button style="width: auto; padding: 0 24px;" onclick="enviarComandoChat()">Enviar</button>
                </div>
                <div id="anexoLabel" style="font-size: 12px; color: var(--success); margin-top: 5px; display: none;"></div>
            </div>
        </div>

        <!-- ABA 4: DISPOSITIVOS & IPS -->
        <div id="tab-dispositivos" class="tab-content">
            <div class="card">
                <h3 class="card-title">Equipamentos Cadastrados e Status de Heartbeat</h3>
                <div id="devicesList" class="grid-3"></div>
            </div>
        </div>

        <!-- ABA 5: AUDITORIA & PERMISSÕES -->
        <div id="tab-auditoria" class="tab-content">
            <div class="grid-2">
                <div class="card">
                    <h3 class="card-title">Usuários Autorizados no Mensageiro</h3>
                    <div id="authorizedUsersList"></div>
                </div>
                <div class="card">
                    <h3 class="card-title">Histórico de Autorizações e Ações</h3>
                    <div id="auditLog" class="log-list"></div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let currentConfig = null;

        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(`tab-${tabId}`).classList.add('active');
        }

        async function requestJson(url, options = {}) {
            const response = await fetch(url, {
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                ...options,
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(data.message || data.reason || `HTTP ${response.status}`);
            }
            return data;
        }

        async function refresh() {
            try {
                const data = await requestJson('/api/config');
                currentConfig = data;
                
                const screens = data.screens || [];
                const selectTela = document.getElementById('selectTela');
                const slideTela = document.getElementById('slideTela');
                
                selectTela.innerHTML = screens.map(s => `<option value="${s}">${s}</option>`).join('');
                slideTela.innerHTML = screens.map(s => `<option value="${s}">${s}</option>`).join('');

                // Galeria de mídias
                const mediaGallery = document.getElementById('mediaGallery');
                mediaGallery.innerHTML = (data.media || []).map(m => `
                    <div class="media-item" onclick="document.getElementById('inputMidia').value='${m}'">
                        <img src="/conteudo/${m}" alt="${m}" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'100\\' height=\\'80\\'><rect width=\\'100%\\' height=\\'100%\\' fill=\\'%231e293b\\'/><text x=\\'50%\\' y=\\'50%\\' fill=\\'%2394a3b8\\' text-anchor=\\'middle\\'>Doc</text></svg>'">
                        <span>${m.replace('biblioteca/', '')}</span>
                    </div>
                `).join('');

                // Dispositivos
                const devicesList = document.getElementById('devicesList');
                devicesList.innerHTML = (data.devices || []).map(d => {
                    const state = (data.state || {})[d.screen_id] || {};
                    const isOnline = d.last_seen_ok;
                    return `
                        <div class="device-card">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                <strong>${d.label || d.screen_id}</strong>
                                <span class="status-badge ${isOnline ? 'badge-online' : 'badge-offline'}">${isOnline ? 'ONLINE' : 'OFFLINE'}</span>
                            </div>
                            <div style="font-size:12px; color:var(--muted); display:grid; gap:4px;">
                                <div><strong>ID:</strong> ${d.screen_id}</div>
                                <div><strong>IP Fixo:</strong> ${d.ip || 'Não definido'}</div>
                                <div><strong>Último Heartbeat:</strong> ${d.last_seen || 'Nenhum'}</div>
                                <div><strong>Estado Atual:</strong> ${state.tipo || 'vazio'} ${state.src ? `(${state.src})` : ''}</div>
                            </div>
                        </div>
                    `;
                }).join('');

                // Usuários Autorizados
                const authUsers = document.getElementById('authorizedUsersList');
                authUsers.innerHTML = (data.authorized_users || []).map(u => `
                    <div style="padding:10px; background:#0f172a; border-radius:8px; margin-bottom:8px; font-size:13px;">
                        <strong>${u.nome || u.user_id}</strong> (${u.role})<br>
                        <span style="color:var(--muted); font-size:11px;">Canal: ${u.canal} | Lib: ${u.autorizado_em || '-'}</span>
                    </div>
                `).join('') || '<div style="color:var(--muted); font-size:13px;">Nenhum usuário cadastrado</div>';

                // Logs de Autorização
                const logs = await requestJson('/api/autorizacoes').catch(() => ({ historico: [] }));
                document.getElementById('auditLog').innerHTML = (logs.historico || []).reverse().map(l => `
                    <div class="log-entry">[${l.timestamp || ''}] ${l.actor || 'sistema'}: ${l.acao || 'evento'} -> ${l.status || 'ok'}</div>
                `).join('');

            } catch (e) {
                document.getElementById('authStatus').innerHTML = '<span class="status-badge badge-offline">Sessão Expirada</span> <a href="/login" style="color:var(--danger);font-size:12px;">Fazer Login</a>';
            }
        }


        async function exibirMidia() {
            try {
                const tela = document.getElementById('selectTela').value;
                const midia = document.getElementById('inputMidia').value;
                await requestJson('/api/comando', { method: 'POST', body: JSON.stringify({ acao: 'exibir', tela, midia }) });
                await refresh();
            } catch (e) { alert('Falha ao exibir: ' + e.message); }
        }

        async function limparTela() {
            try {
                const tela = document.getElementById('selectTela').value;
                await requestJson('/api/comando', { method: 'POST', body: JSON.stringify({ acao: 'limpar', tela }) });
                await refresh();
            } catch (e) { alert('Falha ao limpar: ' + e.message); }
        }

        async function rotacionarTela() {
            try {
                const tela = document.getElementById('selectTela').value;
                await requestJson('/api/comando', { method: 'POST', body: JSON.stringify({ acao: 'rotacionar', tela }) });
                await refresh();
            } catch (e) { alert('Falha ao rotacionar: ' + e.message); }
        }

        async function gerarSlide() {
            try {
                const tela = document.getElementById('slideTela').value;
                const titulo = document.getElementById('slideTitulo').value;
                const corpo = document.getElementById('slideCorpo').value;
                await requestJson('/api/comando', { method: 'POST', body: JSON.stringify({ acao: 'gerar_slide', tela, titulo, corpo }) });
                alert('Cartaz gerado e publicado!');
                await refresh();
            } catch (e) { alert('Falha ao gerar cartaz: ' + e.message); }
        }

        async function enviarComandoChat() {
            const input = document.getElementById('inputChat');
            const anexo = document.getElementById('chatAnexo');
            const texto = input.value.trim();
            if (!texto && (!anexo || !anexo.files.length)) return;

            const history = document.getElementById('chatHistory');
            history.innerHTML += `<div class="chat-msg user">${texto || '[Mídia Anexada]'}</div>`;
            input.value = '';

            const formData = new FormData();
            if (texto) formData.append('texto', texto);
            if (anexo && anexo.files.length > 0) {
                formData.append('midia', anexo.files[0]);
                // Clear the file input immediately
                anexo.value = '';
                document.getElementById('anexoLabel').style.display = 'none';
            }

            try {
                const response = await fetch('/api/comando', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.status === 401) {
                    document.getElementById('authStatus').innerHTML = '<span class="status-badge badge-offline">Desconectado</span>';
                    throw new Error('Sessão expirada. Faça login novamente.');
                }
                
                const res = await response.json();
                if (!response.ok) throw new Error(res.reason || res.message || 'Erro');
                history.innerHTML += `<div class="chat-msg bot">✅ Ação Executada: ${JSON.stringify(res, null, 2)}</div>`;
                await refresh();
            } catch (e) {
                history.innerHTML += `<div class="chat-msg bot" style="background:#451a1a; color:#f87171;">⚠️ Recusado: ${e.message}</div>`;
            }
            history.scrollTop = history.scrollHeight;
        }

        function updateAnexoLabel(inputElement) {
            const label = document.getElementById('anexoLabel');
            if (inputElement.files && inputElement.files.length > 0) {
                label.textContent = `📎 Anexo: ${inputElement.files[0].name}`;
                label.style.display = 'block';
            } else {
                label.style.display = 'none';
            }
        }

        refresh();
    </script>
</body>
</html>"""



VIEWER_HTML = """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Virtual TV - {{ screen_id }}</title>
  <style>
    body, html { margin:0; padding:0; width:100%; height:100%; background:#050814; display:flex; justify-content:center; align-items:center; overflow:hidden; font-family:sans-serif; color:#fff; }
    img { max-width:100%; max-height:100%; object-fit:contain; display:none; border-radius:8px; box-shadow:0 20px 80px rgba(0,0,0,0.8); }
    .placeholder { font-size:24px; text-transform:uppercase; letter-spacing:2px; color:#5e6e8c; text-align:center; padding:20px; }
  </style>
</head>
<body>
  <div id="placeholder" class="placeholder">Carregando Tela Virtual...</div>
  <img id="display" src="" alt="Sinalização Digital">

  <script>
    const screenId = "{{ screen_id }}";
    const img = document.getElementById('display');
    const placeholder = document.getElementById('placeholder');
    let currentSrc = null;

    async function updateScreen() {
      try {
        const response = await fetch(`/api/tela/${screenId}`);
        const data = await response.json();
        const estado = data.estado || {};
        if (estado.tipo === 'vazio' || !estado.src) {
          img.style.display = 'none';
          placeholder.style.display = 'block';
          placeholder.textContent = "Tela do Saguão: Aguardando nova publicação...";
          currentSrc = null;
        } else {
          const srcUrl = `/conteudo/${estado.src}`;
          if (currentSrc !== srcUrl) {
            img.src = srcUrl;
            img.style.display = 'block';
            placeholder.style.display = 'none';
            currentSrc = srcUrl;
          }
        }
      } catch (e) {
        placeholder.style.display = 'block';
        placeholder.textContent = "Erro de conexão com o Gestor";
      }
    }

    setInterval(updateScreen, 2000);
    updateScreen();
  </script>
</body>
</html>"""


LOGIN_HTML = """<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Login • Gestor PicoClaw</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090d16; --panel: rgba(15, 23, 42, 0.85); --panel-border: rgba(255, 255, 255, 0.1);
            --text: #f8fafc; --muted: #94a3b8; --accent: #14b8a6;
            --accent-gradient: linear-gradient(135deg, #0d9488, #2563eb);
            --input-bg: #0f172a;
        }
        * { box-sizing: border-box; }
        body { margin: 0; font-family: 'Inter', sans-serif; background: radial-gradient(ellipse at top, #1e293b 0%, #0f172a 50%, #090d16 100%); color: var(--text); min-height: 100vh; display: flex; justify-content: center; align-items: center; }
        .login-card { background: var(--panel); backdrop-filter: blur(16px); border: 1px solid var(--panel-border); border-radius: 16px; padding: 32px; width: 100%; max-width: 400px; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }
        .logo { text-align: center; margin-bottom: 24px; }
        .logo h1 { font-size: 24px; margin: 0; }
        .logo p { font-size: 13px; color: var(--muted); margin: 4px 0 0 0; }
        .tabs { display: flex; border-bottom: 1px solid var(--panel-border); margin-bottom: 24px; }
        .tab { flex: 1; text-align: center; padding: 12px; cursor: pointer; color: var(--muted); font-weight: 500; border-bottom: 2px solid transparent; transition: 0.2s; }
        .tab.active { color: var(--accent); border-bottom-color: var(--accent); }
        .form-group { margin-bottom: 16px; }
        label { display: block; font-size: 13px; margin-bottom: 6px; color: var(--muted); }
        input { width: 100%; background: var(--input-bg); border: 1px solid var(--panel-border); border-radius: 8px; color: var(--text); padding: 12px; font-family: inherit; outline: none; transition: 0.2s; }
        input:focus { border-color: var(--accent); }
        button { width: 100%; padding: 12px; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; background: var(--accent-gradient); color: #fff; margin-top: 8px; transition: 0.2s; }
        button:hover { opacity: 0.95; }
        .error { color: #ef4444; font-size: 13px; margin-bottom: 16px; text-align: center; display: none; }
        .success { color: #22c55e; font-size: 13px; margin-bottom: 16px; text-align: center; display: none; }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo">
            <h1>TV Box Admin</h1>
            <p>Acesso Restrito ao Diretor</p>
        </div>
        <div class="tabs">
            <div class="tab active" onclick="setMode('login')" id="tab-login">Entrar</div>
            <div class="tab" onclick="setMode('register')" id="tab-register">Cadastrar</div>
        </div>
        <div class="error" id="errorMsg"></div>
        <div class="success" id="successMsg"></div>
        <form id="authForm" onsubmit="submitForm(event)">
            <div class="form-group">
                <label>Usuário</label>
                <input type="text" id="username" required autocomplete="username">
            </div>
            <div class="form-group">
                <label>Senha</label>
                <input type="password" id="password" required autocomplete="current-password">
            </div>
            <button type="submit" id="submitBtn">Entrar no Sistema</button>
        </form>
    </div>

    <script>
        let mode = 'login';
        
        function setMode(newMode) {
            mode = newMode;
            document.getElementById('tab-login').classList.toggle('active', mode === 'login');
            document.getElementById('tab-register').classList.toggle('active', mode === 'register');
            document.getElementById('submitBtn').textContent = mode === 'login' ? 'Entrar no Sistema' : 'Criar Conta de Diretor';
            document.getElementById('errorMsg').style.display = 'none';
            document.getElementById('successMsg').style.display = 'none';
        }

        async function submitForm(e) {
            e.preventDefault();
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;
            const btn = document.getElementById('submitBtn');
            const err = document.getElementById('errorMsg');
            const succ = document.getElementById('successMsg');
            
            btn.disabled = true;
            btn.textContent = 'Aguarde...';
            err.style.display = 'none';
            succ.style.display = 'none';

            try {
                const res = await fetch(`/${mode}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: u, password: p})
                });
                const data = await res.json();
                
                if(res.ok) {
                    if (mode === 'register') {
                        succ.textContent = 'Cadastro realizado! Faça login para entrar.';
                        succ.style.display = 'block';
                        setMode('login');
                        document.getElementById('password').value = '';
                    } else {
                        window.location.href = '/painel';
                    }
                } else {
                    err.textContent = data.message || 'Erro de autenticação';
                    err.style.display = 'block';
                }
            } catch (error) {
                err.textContent = 'Erro de rede. Tente novamente.';
                err.style.display = 'block';
            } finally {
                btn.disabled = false;
                btn.textContent = mode === 'login' ? 'Entrar no Sistema' : 'Criar Conta de Diretor';
            }
        }
    </script>
</body>
</html>"""


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = str(service.settings.get("flask_secret_key", "desenvolvimento-tvb"))

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user"):
                if request.path.startswith("/api"):
                    return jsonify({"status": "erro", "message": "autenticacao requerida"}), 401
                from flask import redirect, url_for
                return redirect(url_for("web_login"))
            return view(*args, **kwargs)
        return wrapped

    @app.get("/")
    def index():
        return jsonify(
            {
                "service": "sinalizacao-gestor",
                "status": "ok",
                "screens": service.available_screens(),
                "media": service.list_media(),
                "polling_segundos": service.settings.get("polling_segundos", 5),
            }
        )

    @app.get("/login")
    def web_login():
        if session.get("user"):
            from flask import redirect, url_for
            return redirect(url_for("painel"))
        return render_template_string(LOGIN_HTML)

    @app.post("/login")
    def process_web_login():
        payload = request.get_json(force=True, silent=True) or {}
        username = str(payload.get("username", ""))
        password = str(payload.get("password", ""))
        if not service.authenticate_local_user(username, password):
            return jsonify({"status": "erro", "message": "Credenciais inválidas"}), 401
        session.clear()
        session["user"] = username
        return jsonify({"status": "ok", "user": username})

    @app.post("/register")
    def process_web_register():
        payload = request.get_json(force=True, silent=True) or {}
        username = str(payload.get("username", ""))
        password = str(payload.get("password", ""))
        if not username or not password:
            return jsonify({"status": "erro", "message": "Dados incompletos"}), 400
        if service.register_local_user(username, password):
            return jsonify({"status": "ok", "message": "Cadastrado com sucesso!"})
        return jsonify({"status": "erro", "message": "Usuário já existe"}), 409

    @app.get("/logout")
    def web_logout():
        session.clear()
        from flask import redirect, url_for
        return redirect(url_for("web_login"))

    @app.get("/painel")
    @login_required
    def painel():
        return render_template_string(PANEL_HTML, username=session.get("user"))

    @app.get("/visualizar/<screen_id>")
    def visualizar(screen_id: str):
        if screen_id not in service.available_screens():
            abort(404)
        return render_template_string(VIEWER_HTML, screen_id=screen_id)

    @app.post("/api/login")
    def login():
        payload = request.get_json(force=True, silent=True) or {}
        username = str(payload.get("user", ""))
        password = str(payload.get("senha", ""))
        if not service.authenticate_local_user(username, password):
            return jsonify({"status": "erro", "message": "credenciais invalidas"}), 401
        session.clear()
        session["user"] = username
        return jsonify({"status": "ok", "user": username})

    @app.post("/api/logout")
    @login_required
    def logout():
        session.clear()
        return jsonify({"status": "ok"})

    @app.get("/api/config")
    @login_required
    def config():
        return jsonify(
            {
                "settings": service.settings,
                "screens": service.available_screens(),
                "state": service.get_state(),
                "media": service.list_media(),
                "authorized_users": service.list_authorized_users(),
                "devices": service.list_devices(),
            }
        )

    @app.get("/api/dispositivos")
    @login_required
    def dispositivos():
        return jsonify({"devices": service.list_devices()})

    @app.post("/api/dispositivos")
    @login_required
    def dispositivo_upsert():
        payload = request.get_json(force=True, silent=True) or {}
        screen_id = str(payload.get("screen_id", "")).strip()
        if not screen_id:
            return jsonify({"status": "recusado", "reason": "screen_id ausente"}), 400

        catalog = service.device_catalog()
        catalog[screen_id] = {
            "screen_id": screen_id,
            "label": str(payload.get("label", screen_id)),
            "ip": str(payload.get("ip", "")).strip(),
            "ativo": bool(payload.get("ativo", True)),
            "device_token": str(payload.get("device_token", "")).strip(),
            "aliases": payload.get("aliases", []),
            "room": payload.get("room"),
        }
        service.device_catalog_store.write(catalog)
        return jsonify({"status": "ok", "device": catalog[screen_id]})

    @app.post("/api/dispositivos/heartbeat")
    def dispositivo_heartbeat():
        payload = request.get_json(force=True, silent=True) or {}
        result = service.register_device_heartbeat(payload, remote_ip=request.remote_addr)
        return jsonify(result), 200 if result.get("status") == "ok" else 404

    @app.get("/api/autorizados")
    @login_required
    def autorizados():
        return jsonify({"autorizados": service.list_authorized_users()})

    @app.get("/api/autorizacoes")
    @login_required
    def autorizacoes():
        return jsonify({"historico": service.list_authorization_history()})

    @app.get("/api/tela/<screen_id>")
    def tela(screen_id: str):
        return jsonify({"tela": screen_id, "estado": service.get_screen_state(screen_id)})

    @app.get("/conteudo/<path:src>")
    def conteudo(src: str):
        try:
            resolved = service._resolve_library_media(src)
        except (FileNotFoundError, ValueError):
            abort(404)
        return send_file(resolved)

    @app.post("/api/comando")
    @login_required
    def comando():
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            texto = request.form.get("texto", "").strip()
            arquivo = request.files.get("midia")
            media_ref = None
            if arquivo and arquivo.filename:
                import os
                from werkzeug.utils import secure_filename
                filename = secure_filename(arquivo.filename)
                upload_path = os.path.join(service.paths.biblioteca_dir, filename)
                arquivo.save(upload_path)
                media_ref = "biblioteca/" + filename
            
            result = service.handle_text_command(texto, origin="painel_local", actor=session.get("user", ""), attachment_path=media_ref)
            return jsonify(result), 200 if result.get("status") == "ok" else 400

        payload = request.get_json(force=True, silent=True) or {}
        if "texto" in payload and payload.get("texto"):
            result = service.handle_text_command(str(payload["texto"]), origin="painel_local", actor=session.get("user", ""))
            return jsonify(result), 200 if result.get("status") == "ok" else 400
        result = service.apply_command(payload, origin="painel_local", actor=session.get("user", ""))
        return jsonify(result), 200 if result.get("status") == "ok" else 400

    @app.post("/api/mensagem")
    @login_required
    def mensagem():
        payload = request.get_json(force=True, silent=True) or {}
        result = service.handle_messenger_payload(payload)
        return jsonify(result), 200 if result.get("status") == "ok" else 400

    @app.post("/api/webhook/telegram")
    def webhook_telegram():
        payload = request.get_json(force=True, silent=True) or {}
        result = service.handle_messenger_payload(payload)
        return jsonify(result), 200 if result.get("status") == "ok" else 400

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(service.settings.get("porta", 8080)), debug=True)
