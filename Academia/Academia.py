# Academia.py
"""
Aplicação Flask completa atualizada:
- Abas responsivas (filtragem client-side)
- Campo 'peso_ultimo' e 'observacoes' nos treinos
- Botões Editar/Excluir/ Criar conta estilizados
- Campo 'Usuário' do login com fundo mais visível
- Rota /health e print(app.url_map)
"""
from flask import Flask, render_template_string, request, redirect, session, send_file, url_for, jsonify
import os, json, copy, traceback
from datetime import datetime
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# ------------- Config -------------
APP_SECRET = os.environ.get("SECRET_KEY", "sua-chave-secreta-aqui")
USUARIOS_JSON = "usuarios.json"
USUARIOS_DIR = "usuarios"
ADMIN_LOGIN = os.environ.get("ADMIN_LOGIN", "Kaio.chagas")
ADMIN_NOME = os.environ.get("ADMIN_NOME", "Kaio")
ADMIN_SOBRENOME = os.environ.get("ADMIN_SOBRENOME", "Chagas")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "wk22z*Ox06")

os.makedirs(USUARIOS_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = APP_SECRET

# ------------- Utilities -------------
def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def load_json_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception:
        return None

def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def usuarios_path():
    return os.path.join(os.getcwd(), USUARIOS_JSON)

def user_data_path(login):
    safe = login.replace("/", "_")
    return os.path.join(os.getcwd(), USUARIOS_DIR, f"{safe}.json")

# ------------- Storage functions -------------
def carregar_usuarios():
    data = load_json_file(usuarios_path())
    return data or {}

def salvar_usuarios(data):
    save_json_file(usuarios_path(), data)

def carregar_dados_usuario(login):
    p = user_data_path(login)
    d = load_json_file(p)
    if d is None:
        return {"abas": [], "treinos": []}
    return d

def salvar_dados_usuario(login, dados):
    p = user_data_path(login)
    save_json_file(p, dados)

# ------------- Ensure admin exists -------------
def ensure_admin_exists():
    users = carregar_usuarios()
    if ADMIN_LOGIN in users:
        changed = False
        if users[ADMIN_LOGIN].get("tipo") != "admin":
            users[ADMIN_LOGIN]["tipo"] = "admin"; changed = True
        if not users[ADMIN_LOGIN].get("ativo", True):
            users[ADMIN_LOGIN]["ativo"] = True; changed = True
        if changed:
            salvar_usuarios(users)
        if load_json_file(user_data_path(ADMIN_LOGIN)) is None:
            salvar_dados_usuario(ADMIN_LOGIN, {"abas": [], "treinos": []})
        return
    users[ADMIN_LOGIN] = {
        "nome": ADMIN_NOME,
        "sobrenome": ADMIN_SOBRENOME,
        "senha": generate_password_hash(ADMIN_PASSWORD),
        "tipo": "admin",
        "ativo": True,
        "data_cadastro": now_iso(),
        "ultimo_acesso": None
    }
    salvar_usuarios(users)
    salvar_dados_usuario(ADMIN_LOGIN, {"abas": [], "treinos": []})

ensure_admin_exists()

# ------------- Decorators -------------
def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        users = carregar_usuarios()
        u = users.get(session["usuario"])
        if not u or u.get("tipo") != "admin":
            return "Acesso negado", 403
        return f(*args, **kwargs)
    return wrapped

# ------------- Merge helper -------------
def merge_dados(existing, incoming):
    existing = copy.deepcopy(existing)
    inc_abas = incoming.get("abas", []) or []
    inc_treinos = incoming.get("treinos", []) or []

    name_to_id = { (a.get("nome","").strip().lower()): a.get("id") for a in existing.get("abas", []) if a.get("nome") }
    existing_aba_ids = [a.get("id",0) for a in existing.get("abas",[])]
    next_aba_id = (max(existing_aba_ids) + 1) if existing_aba_ids else 1

    map_old_to_new = {}
    for a in inc_abas:
        name = (a.get("nome") or "").strip()
        if not name:
            continue
        nl = name.lower()
        if nl in name_to_id:
            map_old_to_new[a.get("id")] = name_to_id[nl]
        else:
            new_id = next_aba_id
            next_aba_id += 1
            existing.setdefault("abas", []).append({"id": new_id, "nome": name})
            name_to_id[nl] = new_id
            map_old_to_new[a.get("id")] = new_id

    existing_treino_ids = [t.get("id",0) for t in existing.get("treinos",[])]
    next_treino_id = (max(existing_treino_ids)+1) if existing_treino_ids else 1

    for t in inc_treinos:
        new = copy.deepcopy(t)
        new["id"] = next_treino_id
        next_treino_id += 1
        old_aba = new.get("aba_id")
        if old_aba in map_old_to_new:
            new["aba_id"] = map_old_to_new[old_aba]
        else:
            new["aba_id"] = int(new.get("aba_id") or 0)
        existing.setdefault("treinos", []).append(new)

    return existing

# ------------- Shared head (styles + theme + scripts) -------------
SHARED_HEAD = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{
  --bg:#121212; --card:#1e1e1e; --text:#fff; --accent:#7c5cff; --muted:#9aa0a6;
  --btn-voltar:#6b7280; --btn-export:#10b981; --btn-import:#2563eb; --btn-merge:#8b5cf6;
}
:root.light{ --bg:#f5f6fb; --card:#fff; --text:#111827; --accent:#4f46e5; --muted:#666; --btn-voltar:#6b7280; --btn-export:#059669; --btn-import:#2563eb; --btn-merge:#7c3aed; }
*{box-sizing:border-box}
html,body{height:100%;margin:0;font-family:Inter, system-ui, -apple-system, "Helvetica Neue", Arial;}
body{background:var(--bg);color:var(--text);display:flex;align-items:flex-start;justify-content:center;padding:24px;}
.container{width:100%;max-width:1100px;margin:0 auto;}
.center-card{background:var(--card);padding:24px;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,0.35);}
.header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:18px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:12px}
.logo{font-size:28px}
.title{font-weight:800;font-size:20px}

/* Header controls: consistent + text aligned */
:root{ --hdr-height:44px; --hdr-minw:86px; --hdr-gap:12px; --btn-radius:10px; --btn-fs:14px; --btn-shadow:0 6px 18px rgba(0,0,0,0.18); }
.actions{display:flex;gap:var(--hdr-gap);align-items:center;flex-wrap:wrap;}
.actions a.action-btn, .actions button.action-btn, .actions label.action-btn, .actions .btn-theme {
  display:inline-flex; align-items:center; justify-content:center;
  height:var(--hdr-height); min-width:var(--hdr-minw); padding:0 14px;
  border-radius:var(--btn-radius); font-weight:700; font-size:var(--btn-fs);
  color:#fff; text-decoration:none; border:none; cursor:pointer; background:transparent;
  box-sizing:border-box; line-height:normal; transition:transform .12s ease, box-shadow .12s ease;
}
.actions label.action-btn{ cursor:pointer; }

/* action color variants */
.btn-voltar{ background:var(--btn-voltar); }
.btn-export{ background:var(--btn-export); }
.btn-import{ background:var(--btn-import); }
.btn-merge{ background:var(--btn-merge); }

/* new specific buttons */
.btn-edit{ background:#4f46e5; }      /* edição: roxo */
.btn-delete{ background:#ef4444; }    /* exclusão: vermelho */
.btn-create{ background:#7c3aed; }    /* criar conta: destaque roxo */

.btn-theme{ background:transparent;color:var(--accent);border:1px solid rgba(255,255,255,0.06); padding:0 12px; min-width:auto; }

/* login field highlight */
#usuario { background:#ffffff; color:#111; border-radius:6px; padding:6px 8px; width:220px; }

/* treino card */
.treino-card{ background: rgba(255,255,255,0.02); padding:12px; border-radius:8px; margin-bottom:12px; border:1px solid rgba(255,255,255,0.03); }

/* ensure direct children consistent */
.actions input[type="file"]{ display:none; }
.actions > *{ display:inline-flex !important; align-items:center !important; justify-content:center !important; margin:0 !important; }
.actions a.action-btn:hover, .actions button.action-btn:hover, .actions label.action-btn:hover { transform:translateY(-2px); box-shadow:var(--btn-shadow); }
.actions a.action-btn:focus, .actions button.action-btn:focus, .actions label.action-btn:focus, .actions .btn-theme:focus { outline:3px solid rgba(124,92,255,0.12); outline-offset:2px; }

.form{max-width:780px;margin:0 auto}
.field{margin-bottom:12px}
label{display:block;font-size:14px;color:var(--muted);margin-bottom:6px}
input[type="text"],input[type="password"],textarea,select{
  width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:transparent;color:var(--text)
}
textarea{resize:vertical;min-height:100px}
button.btn{background:var(--accent);color:white;border:none;padding:10px 14px;border-radius:8px;cursor:pointer;font-weight:700}
.small{padding:6px 10px;font-size:14px}
.aba{display:inline-block;background:var(--accent);color:#fff;padding:8px 14px;border-radius:999px;margin-right:10px;margin-bottom:10px;font-weight:700; cursor:pointer;}
.aba.active{ box-shadow: 0 6px 20px rgba(124,92,255,0.16); transform: translateY(-2px); }
.historico{background:rgba(255,255,255,0.03);padding:12px;border-radius:8px;margin-top:10px}
img{max-width:100%;border-radius:8px;margin-top:8px}
@media (max-width:720px){ .header{flex-direction:column;align-items:flex-start} .title{font-size:18px} .logo{font-size:24px} }
@media (max-width:520px){
  .actions{flex-direction:column;align-items:stretch}
  .actions a.action-btn, .actions button.action-btn, .actions label.action-btn, .actions .btn-theme { width:100%; min-width:0; justify-content:center; }
}
</style>

<script>
// Theme toggle
function initThemeToggle(){
  const root = document.documentElement;
  if(localStorage.getItem('theme')==='light') root.classList.add('light');
  document.addEventListener('click', function(e){
    if(e.target && e.target.matches('[data-toggle-theme]')){
      root.classList.toggle('light');
      localStorage.setItem('theme', root.classList.contains('light') ? 'light' : 'dark');
    }
  });
}

// Client-side tab filtering: mark treino cards with data-aba and toggle visibility
function initAbaFiltering(){
  document.addEventListener('click', function(e){
    if(e.target && e.target.matches('.aba')){
      const aba = e.target.getAttribute('data-aba') || '';
      const all = aba === '' || aba === 'all';
      // toggle active class
      document.querySelectorAll('.aba').forEach(a => a.classList.remove('active'));
      e.target.classList.add('active');

      // show/hide treino cards
      document.querySelectorAll('.treino-card').forEach(card => {
        const cardAba = card.getAttribute('data-aba') || '0';
        if(all || String(cardAba) === String(aba)) card.style.display = '';
        else card.style.display = 'none';
      });

      // update URL param
      if(!all){
        history.pushState(null, '', updateQueryStringParameter(window.location.href, 'aba', aba));
      } else {
        history.pushState(null, '', removeQueryStringParameter(window.location.href, 'aba'));
      }
    }
  });
}

function updateQueryStringParameter(uri, key, value) {
  const re = new RegExp("([?&])" + key + "=.*?(&|$)", "i");
  const separator = uri.indexOf('?') !== -1 ? "&" : "?";
  if (uri.match(re)) return uri.replace(re, '$1' + key + "=" + value + '$2');
  else return uri + separator + key + "=" + value;
}
function removeQueryStringParameter(uri, key) {
  // remove ?aba=... or &aba=...
  return uri.replace(new RegExp("([&?])" + key + "=[^&]*"), function(m, p1){
    if(p1 === '?') return '?';
    return '';
  }).replace(/\?$/, '');
}

document.addEventListener('DOMContentLoaded', function(){
  initThemeToggle();
  initAbaFiltering();
  // Auto-apply aba from URL if present
  const params = new URLSearchParams(window.location.search);
  const aba = params.get('aba');
  if(aba){
    const btn = document.querySelector('.aba[data-aba="'+aba+'"]');
    if(btn) btn.click();
  }
});
</script>
"""

# ------------- Templates -------------
LOGIN_HTML = SHARED_HEAD + """
<div class="container"><div class="center-card">
  <div class="header">
    <div class="brand"><div class="logo">🏋️</div><div><div class="title">Meu Treino</div><div style="font-size:12px;color:var(--muted)">Acesse sua rotina</div></div></div>
    <div class="actions"><a class="action-btn btn-voltar" href="/">Voltar</a><button class="btn-theme" data-toggle-theme>Alternar Tema</button></div>
  </div>
  <div class="form">
    <h2 style="margin-top:0">Entrar</h2>
    {% if mensagem %}<div style="background:rgba(231,76,60,0.08);padding:10px;border-radius:8px;color:var(--danger);margin-bottom:12px">{{ mensagem }}</div>{% endif %}
    <form method="post" action="{{ url_for('login') }}" class="login-form">
      <div class="field"><label for="usuario">Usuário:</label><input id="usuario" type="text" name="usuario" required></div>
      <div class="field"><label for="senha">Senha:</label><input id="senha" type="password" name="senha" required></div>
      <div style="display:flex;gap:10px;align-items:center">
        <button class="btn" type="submit">Entrar</button>
        <a class="action-btn btn-create" href="{{ url_for('registrar') }}">Criar conta</a>
      </div>
    </form>
  </div>
</div></div>
"""

REGISTRO_HTML = SHARED_HEAD + """
<div class="container"><div class="center-card">
  <div class="header"><div class="brand"><div class="logo">🏋️</div><div><div class="title">Meu Treino</div><div style="font-size:12px;color:var(--muted)">Crie sua conta</div></div></div><div class="actions"><a class="action-btn btn-voltar" href="/">Voltar</a><button class="btn-theme" data-toggle-theme>Alternar Tema</button></div></div>
  <div class="form">
    <h2 style="margin-top:0">Registrar</h2>
    {% if mensagem %}<div style="background:rgba(124,92,255,0.08);padding:10px;border-radius:8px;color:var(--accent);margin-bottom:12px">{{ mensagem }}</div>{% endif %}
    <form method="post" action="{{ url_for('registrar') }}">
      <div class="field"><label for="nome">Nome:</label><input id="nome" type="text" name="nome" required></div>
      <div class="field"><label for="sobrenome">Sobrenome:</label><input id="sobrenome" type="text" name="sobrenome" required></div>
      <div class="field"><label for="senha">Senha:</label><input id="senha" type="password" name="senha" required placeholder="Crie uma senha segura"></div>
      <div class="field"><label for="confirmar_senha">Confirmar senha:</label><input id="confirmar_senha" type="password" name="confirmar_senha" required placeholder="Repita a senha"></div>
      <div style="display:flex;gap:10px;align-items:center">
        <button class="btn" type="submit">Criar Conta</button>
        <a class="action-btn btn-voltar" href="{{ url_for('login') }}">Voltar ao Login</a>
      </div>
    </form>
  </div>
</div></div>
"""

MAIN_HTML = SHARED_HEAD + """
<div class="container"><div class="center-card">
  <div class="header">
    <div class="brand"><div class="logo">🏋️</div><div><div class="title">Meu Treino</div><div style="font-size:12px;color:var(--muted)">Bem-vindo(a)</div></div></div>
    <div class="actions">
      <a class="action-btn btn-voltar" href="{{ url_for('criar_treino') }}">Novo</a>
      <a class="action-btn btn-export" href="{{ url_for('exportar') }}">Exportar</a>
      <form method="post" action="{{ url_for('importar') }}" enctype="multipart/form-data" style="display:inline">
        <label class="action-btn btn-import"><input type="file" name="arquivo" accept=".json" style="display:none" onchange="this.form.submit()"> Importar</label>
      </form>
      <form method="post" action="{{ url_for('mesclar') }}" enctype="multipart/form-data" style="display:inline">
        <label class="action-btn btn-merge"><input type="file" name="arquivo" accept=".json" style="display:none" onchange="this.form.submit()"> Mesclar</label>
      </form>
      <a class="action-btn btn-voltar" href="{{ url_for('logout') }}">Sair</a>
      {% if is_admin %}<a class="btn small" href="{{ url_for('admin_dashboard') }}">Admin</a>{% endif %}
      <button class="btn-theme" data-toggle-theme>Alternar Tema</button>
    </div>
  </div>

  {% if mensagem %}<div style="background:rgba(124,92,255,0.08);padding:10px;border-radius:8px;color:var(--accent);margin-bottom:12px">{{ mensagem }}</div>{% endif %}

  <section style="margin-bottom:18px">
    <h3>Abas</h3>
    <div>
      <span class="aba" data-aba="all">Todas</span>
      {% for aba in abas %}
        <span class="aba" data-aba="{{ aba.id }}">{{ aba.nome }}</span>
      {% endfor %}
    </div>
  </section>

  <section>
    <h3>Treinos</h3>
    <div id="treino-list">
      {% if treinos %}
        {% for t in treinos %}
          <div class="treino-card" data-aba="{{ t.aba_id }}">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <strong style="font-size:16px">{{ t.nome }}</strong>
              <div style="display:flex; gap:8px;">
                <a class="action-btn btn-edit" href="{{ url_for('editar', id=t.id) }}">Editar</a>
                <a class="action-btn btn-delete" href="{{ url_for('excluir', id=t.id) }}" onclick="return confirm('Excluir exercício?')">Excluir</a>
              </div>
            </div>
            {% if t.imagem %}
              <img src="{{ t.imagem }}" alt="{{ t.nome }}">
            {% endif %}
            <p style="margin:6px 0;color:var(--muted)">Séries: {{ t.series }} — Reps: {{ t.repeticoes }}</p>
            <p style="margin:6px 0;color:var(--muted)">Último peso: {{ t.get('peso_ultimo','-') }}</p>
            <p style="margin:6px 0;color:var(--muted)">{{ t.get('observacoes','') }}</p>
          </div>
        {% endfor %}
      {% else %}
        <p style="color:var(--muted)">Nenhum treino cadastrado.</p>
      {% endif %}
    </div>
  </section>
</div></div>
"""

CREATE_TREINO_HTML = SHARED_HEAD + """
<div class="container"><div class="center-card">
  <div class="header"><div class="brand"><div class="logo">🏋️</div><div><div class="title">Criar Treino</div><div style="font-size:12px;color:var(--muted)">{{ usuario }}</div></div></div>
  <div class="actions"><a class="action-btn btn-voltar" href="{{ url_for('index') }}">Voltar</a><button class="btn-theme" data-toggle-theme>Alternar Tema</button></div></div>

  <form method="post" action="{{ url_for('criar_treino') }}" style="max-width:720px">
    <div class="field"><label>Nome do treino:</label><input name="nome" required></div>
    <div class="field"><label>URL da imagem (opcional):</label><input name="imagem" placeholder="https://..."></div>
    <div class="field" style="display:flex;gap:8px"><div style="flex:1"><label>Séries</label><input name="series"></div><div style="flex:1"><label>Repetições</label><input name="repeticoes"></div></div>
    <div class="field"><label>Peso (última vez)</label><input name="peso_ultimo" placeholder="ex: 40kg"></div>
    <div class="field"><label>Observações</label><textarea name="observacoes" rows="3"></textarea></div>
    <div style="display:flex;gap:10px;align-items:center">
      <button class="btn" type="submit">Salvar</button>
      <a class="action-btn btn-voltar" href="{{ url_for('index') }}">Cancelar</a>
    </div>
  </form>
</div></div>
"""

# ------------- Routes -------------
@app.route("/health")
def health():
    return "ok", 200

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        usuario = (request.form.get("usuario") or "").strip()
        senha = request.form.get("senha") or ""
        users = carregar_usuarios()
        if usuario not in users:
            return render_template_string(LOGIN_HTML, mensagem="Usuário não encontrado")
        u = users[usuario]
        if not u.get("ativo", True):
            return render_template_string(LOGIN_HTML, mensagem="Usuário bloqueado")
        if not check_password_hash(u["senha"], senha):
            return render_template_string(LOGIN_HTML, mensagem="Senha incorreta")
        session["usuario"] = usuario
        users[usuario]["ultimo_acesso"] = now_iso()
        salvar_usuarios(users)
        if users[usuario].get("tipo")=="admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("index"))
    return render_template_string(LOGIN_HTML)

@app.route("/registrar", methods=["GET","POST"])
def registrar():
    if request.method=="POST":
        nome = (request.form.get("nome") or "").strip()
        sobrenome = (request.form.get("sobrenome") or "").strip()
        senha = request.form.get("senha") or ""
        confirmar = request.form.get("confirmar_senha") or ""
        if not nome or not sobrenome:
            return render_template_string(REGISTRO_HTML, mensagem="Nome e sobrenome são obrigatórios")
        if senha != confirmar:
            return render_template_string(REGISTRO_HTML, mensagem="Senhas não conferem")
        login_name = f"{nome}.{sobrenome}".lower().replace(" ","")
        users = carregar_usuarios()
        if login_name in users:
            return render_template_string(REGISTRO_HTML, mensagem="Este usuário já existe")
        users[login_name] = {"nome":nome,"sobrenome":sobrenome,"senha":generate_password_hash(senha),"tipo":"usuario","ativo":True,"data_cadastro":now_iso(),"ultimo_acesso":None}
        salvar_usuarios(users)
        salvar_dados_usuario(login_name, {"abas": [], "treinos": []})
        return render_template_string(REGISTRO_HTML, mensagem=f"Conta criada com sucesso! Usuário: {login_name}")
    return render_template_string(REGISTRO_HTML)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    dados = carregar_dados_usuario(usuario)
    # server-side filter still applied if param given (progressive enhancement)
    aba_id = request.args.get("aba")
    treinos = dados.get("treinos",[])
    if aba_id and aba_id != 'all':
        treinos = [t for t in treinos if str(t.get("aba_id"))==str(aba_id)]
    users = carregar_usuarios()
    is_admin = users.get(usuario,{}).get("tipo")=="admin"
    return render_template_string(MAIN_HTML, abas=dados.get("abas",[]), treinos=treinos, mensagem=request.args.get("mensagem"), usuario=usuario, is_admin=is_admin)

@app.route("/exportar", methods=["GET"])
def exportar():
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    dados = carregar_dados_usuario(usuario)
    json_str = json.dumps(dados, ensure_ascii=False, indent=4)
    buffer = BytesIO(json_str.encode("utf-8"))
    return send_file(buffer, mimetype="application/json", as_attachment=True, download_name=f"{usuario}_treinos.json")

@app.route("/importar", methods=["POST"])
def importar():
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    arquivo = request.files.get("arquivo")
    if not arquivo or arquivo.filename == "":
        return redirect(url_for("index", mensagem="Nenhum arquivo selecionado"))
    try:
        conteudo = json.loads(arquivo.read().decode("utf-8"))
    except Exception:
        return redirect(url_for("index", mensagem="Arquivo JSON inválido"))
    if "abas" not in conteudo or "treinos" not in conteudo:
        return redirect(url_for("index", mensagem="Estrutura inválida"))
    salvar_dados_usuario(usuario, conteudo)
    return redirect(url_for("index", mensagem="Dados importados com sucesso!"))

@app.route("/mesclar", methods=["POST"])
def mesclar():
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    arquivo = request.files.get("arquivo")
    if not arquivo or arquivo.filename == "":
        return redirect(url_for("index", mensagem="Nenhum arquivo selecionado"))
    try:
        conteudo = json.loads(arquivo.read().decode("utf-8"))
    except Exception:
        return redirect(url_for("index", mensagem="Arquivo JSON inválido"))
    if "abas" not in conteudo or "treinos" not in conteudo:
        return redirect(url_for("index", mensagem="Estrutura inválida"))
    atuais = carregar_dados_usuario(usuario)
    merged = merge_dados(atuais, conteudo)
    salvar_dados_usuario(usuario, merged)
    return redirect(url_for("index", mensagem="Dados mesclados com sucesso!"))

@app.route("/criar_aba_ajax", methods=["POST"])
def criar_aba_ajax():
    if "usuario" not in session:
        return jsonify({"error":"not authenticated"}), 401
    payload = request.get_json() if request.is_json else request.form.to_dict()
    nome = (payload.get("nome") or "").strip()
    if not nome:
        return jsonify({"error":"nome vazio"}), 400
    dados = carregar_dados_usuario(session["usuario"])
    existing_ids = [a.get("id",0) for a in dados.get("abas",[])]
    next_id = max(existing_ids)+1 if existing_ids else 1
    aba = {"id": next_id, "nome": nome}
    dados.setdefault("abas", []).append(aba)
    salvar_dados_usuario(session["usuario"], dados)
    return jsonify(aba), 200

@app.route("/criar_treino", methods=["GET","POST"])
def criar_treino():
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    if request.method=="POST":
        nome = (request.form.get("nome") or "").strip()
        if not nome:
            return redirect(url_for("criar_treino"))
        dados = carregar_dados_usuario(usuario)
        treino_ids = [t.get("id",0) for t in dados.get("treinos",[])]
        novo_id = max(treino_ids)+1 if treino_ids else 1
        treino = {
            "id": novo_id,
            "aba_id": int(request.form.get("aba_id") or 0),
            "nome": nome,
            "imagem": request.form.get("imagem",""),
            "series": request.form.get("series",""),
            "repeticoes": request.form.get("repeticoes",""),
            "peso_ultimo": request.form.get("peso_ultimo",""),
            "observacoes": request.form.get("observacoes",""),
            "historico": []
        }
        dados.setdefault("treinos",[]).append(treino)
        salvar_dados_usuario(usuario, dados)
        return redirect(url_for("index"))
    dados = carregar_dados_usuario(session["usuario"])
    return render_template_string(CREATE_TREINO_HTML, abas=dados.get("abas",[]), usuario=session["usuario"])

@app.route("/editar/<int:id>", methods=["GET","POST"])
def editar(id):
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    dados = carregar_dados_usuario(usuario)
    treino = next((t for t in dados.get("treinos",[]) if t.get("id")==id), None)
    if not treino:
        return "Treino não encontrado", 404
    if request.method=="POST":
        treino["nome"] = request.form.get("nome", treino.get("nome"))
        treino["imagem"] = request.form.get("imagem", treino.get("imagem"))
        treino["series"] = request.form.get("series", treino.get("series"))
        treino["repeticoes"] = request.form.get("repeticoes", treino.get("repeticoes"))
        treino["peso_ultimo"] = request.form.get("peso_ultimo", treino.get("peso_ultimo",""))
        treino["observacoes"] = request.form.get("observacoes", treino.get("observacoes",""))
        salvar_dados_usuario(usuario, dados)
        return redirect(url_for("index"))
    # simple form to edit including new fields
    return f"""
      <form method='post' style='font-family:Arial;color:#fff;'>
        Nome:<br><input name='nome' value="{treino.get('nome','')}" style='width:100%;padding:8px;margin-bottom:8px;'><br>
        Imagem URL:<br><input name='imagem' value="{treino.get('imagem','')}" style='width:100%;padding:8px;margin-bottom:8px;'><br>
        Séries:<br><input name='series' value="{treino.get('series','')}" style='padding:8px;margin-bottom:8px;'><br>
        Repetições:<br><input name='repeticoes' value="{treino.get('repeticoes','')}" style='padding:8px;margin-bottom:8px;'><br>
        Peso (última vez):<br><input name='peso_ultimo' value="{treino.get('peso_ultimo','')}" style='padding:8px;margin-bottom:8px;'><br>
        Observações:<br><textarea name='observacoes' style='width:100%;height:120px;padding:8px;margin-bottom:8px;'>{treino.get('observacoes','')}</textarea><br>
        <button type='submit' style='padding:10px 14px;background:#4f46e5;color:#fff;border:none;border-radius:6px;'>Salvar</button>
      </form>
    """

@app.route("/excluir/<int:id>")
def excluir(id):
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    dados = carregar_dados_usuario(usuario)
    dados["treinos"] = [t for t in dados.get("treinos",[]) if t.get("id")!=id]
    salvar_dados_usuario(usuario, dados)
    return redirect(url_for("index"))

# --- Admin routes (kept similar) ---
@app.route("/admin")
@admin_required
def admin_dashboard():
    users = carregar_usuarios()
    total = len(users)
    ativos = sum(1 for u in users.values() if u.get("ativo",True))
    bloqueados = total - ativos
    total_treinos = sum(len(carregar_dados_usuario(login).get("treinos",[])) for login in users.keys())
    recent_regs = sorted(users.items(), key=lambda kv: kv[1].get("data_cadastro",""), reverse=True)[:5]
    recent_access = sorted(users.items(), key=lambda kv: kv[1].get("ultimo_acesso") or "", reverse=True)[:5]
    return render_template_string(SHARED_HEAD + """
    <div class="container"><div class="center-card">
      <div class="header"><div class="brand"><div class="logo">🏋️</div><div><div class="title">Meu Treino — Admin</div><div style="font-size:12px;color:var(--muted)">Painel administrativo</div></div></div>
      <div class="actions"><a class="action-btn btn-export" href="{{ url_for('admin_usuarios') }}">Gerenciar Usuários</a><a class="action-btn btn-voltar" href='{{ url_for("index") }}'>Voltar</a><button class="btn-theme" data-toggle-theme>Alternar Tema</button></div></div>
      <div style="display:flex;gap:18px;flex-wrap:wrap"><div style="flex:1;min-width:220px">
      <h3>Resumo</h3><ul style="color:var(--muted)"><li>Total de usuários: {{ total }}</li><li>Usuários ativos: {{ ativos }}</li><li>Usuários bloqueados: {{ bloqueados }}</li><li>Total de treinos: {{ total_treinos }}</li></ul></div>
      <div style="flex:2;min-width:300px"><h3>Últimos registros</h3><ul style="color:var(--muted)">{% for login, meta in recent_regs %}<li>{{ login }} — {{ meta.get('data_cadastro','-') }}</li>{% endfor %}</ul><h3>Últimos acessos</h3><ul style="color:var(--muted)">{% for login, meta in recent_access %}<li>{{ login }} — {{ meta.get('ultimo_acesso','-') }}</li>{% endfor %}</ul></div></div></div></div>
    """, total=total, ativos=ativos, bloqueados=bloqueados, total_treinos=total_treinos, recent_regs=recent_regs, recent_access=recent_access)

@app.route("/admin/usuarios")
@admin_required
def admin_usuarios():
    try:
        q = (request.args.get("q") or "").strip().lower()
        users = carregar_usuarios()
        items = []
        for login, meta in users.items():
            if q:
                if q not in login.lower() and q not in meta.get("nome","").lower() and q not in meta.get("sobrenome","").lower():
                    continue
            items.append((login, meta))
        items_sorted = sorted(items, key=lambda kv: kv[0].lower())
        return render_template_string(SHARED_HEAD + """
        <div class="container"><div class="center-card">
          <div class="header"><div class="brand"><div class="logo">🏋️</div><div><div class="title">Usuários</div><div style="font-size:12px;color:var(--muted)">Gerenciar contas</div></div></div>
          <div class="actions"><a class="action-btn btn-export" href="{{ url_for('admin_dashboard') }}">Dashboard</a><button class="btn-theme" data-toggle-theme>Alternar Tema</button></div></div>
          <form method="get" action="{{ url_for('admin_usuarios') }}" style="margin-bottom:12px"><input name="q" placeholder="Pesquisar..." value="{{ query }}" style="padding:8px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);width:60%;max-width:360px"><button class="btn small" type="submit">Pesquisar</button><a href="{{ url_for('admin_usuarios') }}" class="action-btn btn-voltar" style="margin-left:8px">Limpar</a></form>
          <div style="overflow:auto"><table border="0" cellpadding="8" style="width:100%;border-collapse:collapse;color:var(--text)"><thead style="text-align:left;color:var(--muted)"><tr><th>Usuário</th><th>Nome</th><th>Tipo</th><th>Status</th><th>Cadastro</th><th>Último acesso</th><th>Ações</th></tr></thead><tbody>{% for login, meta in users %}<tr style="border-top:1px solid rgba(255,255,255,0.03)"><td>{{ login }}</td><td>{{ meta.get('nome','') }} {{ meta.get('sobrenome','') }}</td><td>{{ meta.get('tipo','') }}</td><td>{{ 'Ativo' if meta.get('ativo',True) else 'Bloqueado' }}</td><td>{{ meta.get('data_cadastro','-') }}</td><td>{{ meta.get('ultimo_acesso','-') }}</td><td><a class="action-btn btn-export" href='{{ url_for("admin_ver_treinos", login=login) }}'>Ver</a> <a class="action-btn btn-merge" href='{{ url_for("admin_editar_usuario", login=login) }}'>Editar</a> {% if meta.get('ativo',True) %}<form style="display:inline" method="post" action="{{ url_for('admin_bloquear', login=login) }}"><button class="action-btn btn-merge" type="submit">Bloquear</button></form>{% else %}<form style="display:inline" method="post" action="{{ url_for('admin_desbloquear', login=login) }}"><button class="action-btn btn-export" type="submit">Desbloquear</button></form>{% endif %} {% if login != ADMIN_LOGIN %}<form style="display:inline" method="post" action="{{ url_for('admin_excluir', login=login) }}" onsubmit="return confirm('Confirma exclusão de ' + '{{login}}' + ' ?');"><button class="action-btn btn-voltar" type="submit">Excluir</button></form>{% endif %} <form style="display:inline" method="post" action='{{ url_for("admin_reset_senha", login=login) }}'><input type="password" name="nova_senha" placeholder="Nova senha" style="padding:6px;border-radius:6px;border:1px solid rgba(255,255,255,0.06)"><button class="action-btn btn-import" type="submit">Resetar</button></form></td></tr>{% endfor %}</tbody></table></div><p style="margin-top:12px"><a class="action-btn btn-voltar" href="{{ url_for('admin_dashboard') }}">Voltar ao Dashboard</a></p></div></div>
        """, users=items_sorted, query=q, ADMIN_LOGIN=ADMIN_LOGIN)
    except Exception:
        tb = traceback.format_exc()
        print("ERROR in admin_usuarios:", tb)
        return "Erro interno ao listar usuários. Verifique os logs do servidor.", 500

@app.route("/admin/usuario/editar/<login>", methods=["GET","POST"])
@admin_required
def admin_editar_usuario(login):
    users = carregar_usuarios()
    if login not in users:
        return "Usuário não encontrado", 404
    meta = users[login]
    if request.method == "POST":
        novo_login = (request.form.get("login") or "").strip()
        nome = (request.form.get("nome") or "").strip()
        sobrenome = (request.form.get("sobrenome") or "").strip()
        tipo = (request.form.get("tipo") or meta.get("tipo"))
        ativo = request.form.get("ativo") == "on"
        nova_senha = (request.form.get("nova_senha") or "").strip()
        if login == ADMIN_LOGIN:
            tipo = "admin"; ativo = True
        if not novo_login:
            return render_template_string(SHARED_HEAD + ADMIN_EDIT_TREINO_HTML, login=login, meta=meta, mensagem="Login inválido")
        users = carregar_usuarios()
        meta = users.pop(login)
        meta["nome"]=nome; meta["sobrenome"]=sobrenome; meta["tipo"]=tipo; meta["ativo"]=bool(ativo)
        if nova_senha: meta["senha"]=generate_password_hash(nova_senha)
        if novo_login != login:
            if novo_login in users:
                users[login]=meta; salvar_usuarios(users)
                return render_template_string(SHARED_HEAD + ADMIN_EDIT_TREINO_HTML, login=login, meta=meta, mensagem="Novo login já existe")
            old_path = user_data_path(login); new_path = user_data_path(novo_login)
            if os.path.exists(old_path): os.replace(old_path, new_path)
            users[novo_login]=meta
        else:
            users[login]=meta
        salvar_usuarios(users)
        return redirect(url_for("admin_usuarios"))
    return render_template_string(SHARED_HEAD + ADMIN_EDIT_TREINO_HTML, login=login, meta=meta, mensagem=None)

@app.route("/admin/usuario/reset_senha/<login>", methods=["POST"])
@admin_required
def admin_reset_senha(login):
    if login==ADMIN_LOGIN:
        return "Não é permitido alterar a senha do admin por aqui.", 403
    nova = (request.form.get("nova_senha") or "").strip()
    if not nova:
        return redirect(url_for("admin_usuarios"))
    users = carregar_usuarios()
    if login not in users: return "Usuário não encontrado", 404
    users[login]["senha"] = generate_password_hash(nova)
    salvar_usuarios(users)
    return redirect(url_for("admin_usuarios"))

@app.route("/admin/usuario/bloquear/<login>", methods=["POST"])
@admin_required
def admin_bloquear(login):
    if login==ADMIN_LOGIN: return "Não é permitido bloquear o admin.", 403
    users = carregar_usuarios()
    if login not in users: return "Usuário não encontrado", 404
    users[login]["ativo"]=False; salvar_usuarios(users)
    return redirect(url_for("admin_usuarios"))

@app.route("/admin/usuario/desbloquear/<login>", methods=["POST"])
@admin_required
def admin_desbloquear(login):
    users = carregar_usuarios()
    if login not in users: return "Usuário não encontrado", 404
    users[login]["ativo"]=True; salvar_usuarios(users)
    return redirect(url_for("admin_usuarios"))

@app.route("/admin/usuario/excluir/<login>", methods=["POST"])
@admin_required
def admin_excluir(login):
    if login==ADMIN_LOGIN: return "Não é permitido excluir o admin.", 403
    users = carregar_usuarios()
    if login not in users: return "Usuário não encontrado", 404
    users.pop(login); salvar_usuarios(users)
    p = user_data_path(login)
    if os.path.exists(p): os.remove(p)
    return redirect(url_for("admin_usuarios"))

@app.route("/admin/usuario/treinos/<login>")
@admin_required
def admin_ver_treinos(login):
    users = carregar_usuarios()
    if login not in users: return "Usuário não encontrado", 404
    dados = carregar_dados_usuario(login)
    return render_template_string(VIEW_TRAINING_HTML, login=login, dados=dados)

@app.route("/admin/usuario/<login>/exportar")
@admin_required
def admin_exportar_usuario(login):
    users = carregar_usuarios()
    if login not in users: return "Usuário não encontrado", 404
    dados = carregar_dados_usuario(login)
    json_str = json.dumps(dados, ensure_ascii=False, indent=4)
    buffer = BytesIO(json_str.encode("utf-8"))
    return send_file(buffer, mimetype="application/json", as_attachment=True, download_name=f"{login}_treinos.json")

@app.route("/admin/usuario/<login>/importar", methods=["POST"])
@admin_required
def admin_importar_usuario(login):
    users = carregar_usuarios()
    if login not in users: return "Usuário não encontrado", 404
    arquivo = request.files.get("arquivo")
    if not arquivo or arquivo.filename == "": return redirect(url_for("admin_ver_treinos", login=login))
    try:
        conteudo = json.loads(arquivo.read().decode("utf-8"))
    except Exception:
        return redirect(url_for("admin_ver_treinos", login=login))
    if "abas" not in conteudo or "treinos" not in conteudo:
        return redirect(url_for("admin_ver_treinos", login=login))
    salvar_dados_usuario(login, conteudo)
    return redirect(url_for("admin_ver_treinos", login=login))

@app.route("/admin/usuario/<login>/mesclar", methods=["POST"])
@admin_required
def admin_mesclar_usuario(login):
    users = carregar_usuarios()
    if login not in users: return "Usuário não encontrado", 404
    arquivo = request.files.get("arquivo")
    if not arquivo or arquivo.filename == "": return redirect(url_for("admin_ver_treinos", login=login))
    try:
        conteudo = json.loads(arquivo.read().decode("utf-8"))
    except Exception:
        return redirect(url_for("admin_ver_treinos", login=login))
    if "abas" not in conteudo or "treinos" not in conteudo:
        return redirect(url_for("admin_ver_treinos", login=login))
    atuais = carregar_dados_usuario(login)
    merged = merge_dados(atuais, conteudo)
    salvar_dados_usuario(login, merged)
    return redirect(url_for("admin_ver_treinos", login=login))

@app.route("/admin/usuario/<login>/treino/criar", methods=["GET","POST"])
@admin_required
def admin_criar_treino(login):
    users = carregar_usuarios()
    if login not in users: return "Usuário não encontrado", 404
    if request.method=="POST":
        dados = carregar_dados_usuario(login)
        novo_id = max((t.get("id",0) for t in dados.get("treinos",[])), default=0) + 1
        treino = {
            "id": novo_id,
            "aba_id": int(request.form.get("aba_id") or 0),
            "nome": request.form.get("nome",""),
            "imagem": request.form.get("imagem",""),
            "series": request.form.get("series",""),
            "repeticoes": request.form.get("repeticoes",""),
            "peso_ultimo": request.form.get("peso_ultimo",""),
            "observacoes": request.form.get("observacoes",""),
            "historico": []
        }
        dados.setdefault("treinos",[]).append(treino)
        salvar_dados_usuario(login, dados)
        return redirect(url_for("admin_ver_treinos", login=login))
    return render_template_string(ADMIN_EDIT_TREINO_HTML, login=login, treino=None, mensagem=None)

@app.route("/admin/usuario/<login>/treino/<int:treino_id>/editar", methods=["GET","POST"])
@admin_required
def admin_editar_treino(login, treino_id):
    users = carregar_usuarios()
    if login not in users: return "Usuário não encontrado", 404
    dados = carregar_dados_usuario(login)
    treino = next((t for t in dados.get("treinos",[]) if t.get("id")==treino_id), None)
    if not treino: return "Treino não encontrado", 404
    if request.method=="POST":
        treino["nome"] = request.form.get("nome", treino.get("nome"))
        treino["aba_id"] = int(request.form.get("aba_id") or treino.get("aba_id",0))
        treino["imagem"] = request.form.get("imagem", treino.get("imagem"))
        treino["series"] = request.form.get("series", treino.get("series"))
        treino["repeticoes"] = request.form.get("repeticoes", treino.get("repeticoes"))
        treino["peso_ultimo"] = request.form.get("peso_ultimo", treino.get("peso_ultimo",""))
        treino["observacoes"] = request.form.get("observacoes", treino.get("observacoes",""))
        salvar_dados_usuario(login, dados)
        return redirect(url_for("admin_ver_treinos", login=login))
    return render_template_string(ADMIN_EDIT_TREINO_HTML, login=login, treino=treino, mensagem=None)

# Print URL map for debugging
print("URL map:", app.url_map)

# ------------- Run -------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
