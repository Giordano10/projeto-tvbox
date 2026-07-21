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
    <title>Painel TV Box</title>
    <style>
        :root { color-scheme: dark; --bg:#0b1020; --panel:#121a33; --line:#253156; --text:#eef2ff; --muted:#9aa7c7; --accent:#5eead4; --accent2:#60a5fa; --danger:#f87171; }
        * { box-sizing:border-box; }
        body { margin:0; font-family: Arial, sans-serif; background: radial-gradient(circle at top, #182544 0, #0b1020 45%, #060913 100%); color:var(--text); }
        header { padding:28px 20px 14px; max-width:1200px; margin:0 auto; }
        h1 { margin:0 0 8px; font-size: clamp(24px, 3vw, 40px); }
        .sub { color:var(--muted); margin:0; }
        main { max-width:1200px; margin:0 auto; padding:0 20px 32px; display:grid; grid-template-columns: 1.2fr 0.9fr; gap:16px; }
        .card { background:rgba(18,26,51,.92); border:1px solid var(--line); border-radius:18px; padding:18px; box-shadow:0 18px 50px rgba(0,0,0,.28); }
        .grid { display:grid; gap:12px; }
        label { display:block; font-size:12px; color:var(--muted); margin-bottom:6px; }
        input, select, textarea, button { width:100%; border-radius:12px; border:1px solid var(--line); background:#0b1226; color:var(--text); padding:12px 14px; font-size:14px; }
        textarea { min-height:110px; resize:vertical; }
        button { cursor:pointer; background:linear-gradient(135deg, var(--accent2), var(--accent)); color:#05111a; font-weight:700; border:none; }
        button.secondary { background:#19213a; color:var(--text); border:1px solid var(--line); }
        button.danger { background:linear-gradient(135deg, #ef4444, #fb7185); color:#fff; }
        .row { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
        .status { margin-top:12px; padding:12px 14px; border-radius:12px; background:#0b1226; border:1px solid var(--line); color:var(--muted); white-space:pre-wrap; }
        .list { display:grid; gap:10px; }
        .item { padding:12px 14px; border-radius:12px; background:#0b1226; border:1px solid var(--line); }
        .item strong { display:block; margin-bottom:4px; }
        .pill { display:inline-block; margin-left:8px; padding:2px 8px; border-radius:999px; background:rgba(94,234,212,.15); color:var(--accent); font-size:12px; }
        code { background:#09101f; padding:2px 6px; border-radius:6px; }
        @media (max-width: 900px) { main { grid-template-columns:1fr; } }
    </style>
</head>
<body>
    <header>
        <h1>Painel local de testes</h1>
        <p class="sub">Use esta tela para autenticar, disparar comandos e conferir o estado das TVs cadastradas na rede local.</p>
    </header>
    <main>
        <section class="card">
            <div class="grid">
                <div class="row">
                    <div>
                        <label for="user">Usuario</label>
                        <input id="user" value="diretor" autocomplete="username">
                    </div>
                    <div>
                        <label for="senha">Senha</label>
                        <input id="senha" type="password" value="trocar123" autocomplete="current-password">
                    </div>
                </div>
                <div class="row">
                    <button id="btnLogin">Entrar</button>
                    <button id="btnRefresh" class="secondary">Atualizar estado</button>
                </div>
                <div>
                    <label for="tela">Tela</label>
                    <select id="tela"></select>
                </div>
                <div>
                    <label for="midia">Midia da biblioteca</label>
                    <input id="midia" placeholder="biblioteca/arquivo.png" value="biblioteca/avisos.png">
                </div>
                <div class="row">
                    <button id="btnExibir">Exibir midia</button>
                    <button id="btnLimpar" class="danger">Limpar tela</button>
                </div>
                <div>
                    <label for="comando">Comando livre</label>
                    <textarea id="comando" placeholder="coloca o aviso da reuniao na tv_saguao"></textarea>
                </div>
                <button id="btnComando" class="secondary">Executar comando textual</button>
            </div>
            <div class="status" id="status">Aguardando login...</div>
        </section>

        <aside class="card">
            <h2 style="margin-top:0">Telas e dispositivos</h2>
            <div class="list" id="devices"></div>
        </aside>
    </main>

    <script>
        const statusBox = document.getElementById('status');
        const devicesBox = document.getElementById('devices');
        const telaSelect = document.getElementById('tela');

        function setStatus(message) {
            statusBox.textContent = message;
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
            const data = await requestJson('/api/config');
            const screens = data.screens || [];
            const devices = data.devices || [];
            telaSelect.innerHTML = screens.map((screen) => `<option value="${screen}">${screen}</option>`).join('');
            devicesBox.innerHTML = devices.map((device) => {
                const state = (data.state || {})[device.screen_id] || {};
                return `<div class="item"><strong>${device.label || device.screen_id}<span class="pill">${device.screen_id}</span></strong>IP: ${device.ip || '-'}<br>Heartbeat: ${device.last_seen || 'nunca'}<br>Estado: ${state.tipo || 'vazio'}${state.src ? `<br>Src: ${state.src}` : ''}</div>`;
            }).join('');
            setStatus(`Logado como ${data.settings ? 'usuario autenticado' : 'visitante'}. ${devices.length} dispositivo(s) carregado(s).`);
        }

        document.getElementById('btnLogin').addEventListener('click', async () => {
            try {
                const payload = { user: document.getElementById('user').value, senha: document.getElementById('senha').value };
                await requestJson('/api/login', { method: 'POST', body: JSON.stringify(payload) });
                setStatus('Login efetuado.');
                await refresh();
            } catch (error) {
                setStatus(`Falha no login: ${error.message}`);
            }
        });

        document.getElementById('btnRefresh').addEventListener('click', async () => {
            try {
                await refresh();
            } catch (error) {
                setStatus(`Falha ao atualizar: ${error.message}`);
            }
        });

        document.getElementById('btnExibir').addEventListener('click', async () => {
            try {
                const payload = { acao: 'exibir', midia: document.getElementById('midia').value, tela: telaSelect.value };
                const result = await requestJson('/api/comando', { method: 'POST', body: JSON.stringify(payload) });
                setStatus(JSON.stringify(result, null, 2));
                await refresh();
            } catch (error) {
                setStatus(`Falha ao exibir: ${error.message}`);
            }
        });

        document.getElementById('btnLimpar').addEventListener('click', async () => {
            try {
                const payload = { acao: 'limpar', tela: telaSelect.value };
                const result = await requestJson('/api/comando', { method: 'POST', body: JSON.stringify(payload) });
                setStatus(JSON.stringify(result, null, 2));
                await refresh();
            } catch (error) {
                setStatus(`Falha ao limpar: ${error.message}`);
            }
        });

        document.getElementById('btnComando').addEventListener('click', async () => {
            try {
                const payload = { texto: document.getElementById('comando').value };
                const result = await requestJson('/api/comando', { method: 'POST', body: JSON.stringify(payload) });
                setStatus(JSON.stringify(result, null, 2));
                await refresh();
            } catch (error) {
                setStatus(`Falha no comando: ${error.message}`);
            }
        });

        refresh().catch((error) => setStatus(`Sem sessao ativa: ${error.message}`));
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


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = str(service.settings.get("flask_secret_key", "desenvolvimento-tvb"))

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user"):
                return jsonify({"status": "erro", "message": "autenticacao requerida"}), 401
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

    @app.get("/painel")
    def painel():
        return render_template_string(PANEL_HTML)

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
        if not service.authenticate_local(username, password):
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

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(service.settings.get("porta", 8080)), debug=True)
