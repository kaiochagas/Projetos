# app.py
"""
Aplicação Flask completa (arquivo único) com:
- Autenticação com hash de senha (werkzeug.security)
- Criação automática do admin Kaio.chagas (senha: wk22z*Ox06)
- Persistência local em arquivos:
    - usuarios.json
    - usuarios/<login>.json
- Painel administrativo: listar, pesquisar, editar, bloquear/desbloquear, excluir usuários,
  resetar senha, visualizar/editar treinos (CRUD).
- Regras de segurança: admin protegido de exclusão/bloqueio/perda de permissão.
- Interfaces simples via templates inline (render_template_string) para uso imediato.
"""

from flask import Flask, request, redirect, session, send_file, render_template_string, url_for, abort
import os
import json
from datetime import datetime
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import shutil

# ----------------------------
# Configurações
# ----------------------------
APP_SECRET = os.environ.get("SECRET_KEY", "sua-chave-secreta-aqui")
USUARIOS_JSON = "usuarios.json"
USUARIOS_DIR = "usuarios"  # armazenará <login>.json
ADMIN_LOGIN = os.environ.get("ADMIN_LOGIN", "Kaio.chagas")  # chave/usuário exato do admin
ADMIN_NOME = os.environ.get("ADMIN_NOME", "Kaio")
ADMIN_SOBRENOME = os.environ.get("ADMIN_SOBRENOME", "Chagas")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "wk22z*Ox06")

os.makedirs(USUARIOS_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = APP_SECRET

# ----------------------------
# Utilitários
# ----------------------------
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

# ----------------------------
# Operações de usuários (metadados)
# ----------------------------
def carregar_usuarios():
    data = load_json_file(usuarios_path())
    if data is None:
        return {}
    return data

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

def ensure_admin_exists():
    users = carregar_usuarios()
    if ADMIN_LOGIN in users:
        # enforce invariants
        changed = False
        if users[ADMIN_LOGIN].get("tipo") != "admin":
            users[ADMIN_LOGIN]["tipo"] = "admin"
            changed = True
        if not users[ADMIN_LOGIN].get("ativo", True):
            users[ADMIN_LOGIN]["ativo"] = True
            changed = True
        if changed:
            salvar_usuarios(users)
        # ensure data file exists
        if load_json_file(user_data_path(ADMIN_LOGIN)) is None:
            salvar_dados_usuario(ADMIN_LOGIN, {"abas": [], "treinos": []})
        return
    # create admin
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

# Guarantee admin on startup
ensure_admin_exists()

def count_admins(users):
    return sum(1 for u in users.values() if u.get("tipo") == "admin")

# ----------------------------
# Decorator de rota admin
# ----------------------------
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

# ----------------------------
# Templates (inline para arquivo único)
# ----------------------------
LOGIN_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Login</title></head>
<body style="font-family:Arial;padding:20px;">
  <h1>Login</h1>
  {% if mensagem %}
    <div style="padding:10px;background:#fdd;border:1px solid #f99;margin-bottom:10px;">{{ mensagem }}</div>
  {% endif %}
  <form method="post" action="{{ url_for('login') }}">
    <label>Usuário: <input type="text" name="usuario" required></label><br><br>
    <label>Senha: <input type="password" name="senha" required></label><br><br>
    <button type="submit">Entrar</button>
  </form>
  <p><a href="{{ url_for('registrar') }}">Criar conta</a></p>
</body>
</html>
"""

REGISTRO_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Registrar</title></head>
<body style="font-family:Arial;padding:20px;">
  <h1>Criar Conta</h1>
  {% if mensagem %}
    <div style="padding:10px;background:#fdd;border:1px solid #f99;margin-bottom:10px;">{{ mensagem }}</div>
  {% endif %}
  <form method="post" action="{{ url_for('registrar') }}">
    <label>Nome: <input name="nome" required></label><br><br>
    <label>Sobrenome: <input name="sobrenome" required></label><br><br>
    <label>Senha: <input type="password" name="senha" required></label><br><br>
    <label>Confirmar Senha: <input type="password" name="confirmar_senha" required></label><br><br>
    <button type="submit">Criar</button>
  </form>
  <p><a href="{{ url_for('login') }}">Voltar ao login</a></p>
</body>
</html>
"""

MAIN_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Meu Treino</title></head>
<body style="font-family:Arial;padding:20px;background:#121212;color:#fff;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <h1>🏋️ Meu Treino</h1>
    <div>
      <span>👤 {{ usuario }}</span>
      <a href="{{ url_for('logout') }}" style="color:#fff;margin-left:10px;">Sair</a>
      {% if is_admin %}
        <a href="{{ url_for('admin_dashboard') }}" style="color:#fff;margin-left:10px;">Painel Admin</a>
      {% endif %}
    </div>
  </div>

  {% if mensagem %}
    <div style="padding:10px;background:#0a0;margin:10px 0;color:#000;">{{ mensagem }}</div>
  {% endif %}

  <section style="margin-top:20px;">
    <h2>Abas</h2>
    {% if abas %}
      <ul>
        {% for aba in abas %}
          <li>{{ aba.nome }}</li>
        {% endfor %}
      </ul>
    {% else %}
      <p>Nenhuma aba criada.</p>
    {% endif %}
  </section>

  <section style="margin-top:20px;">
    <h2>Treinos</h2>
    {% if treinos %}
      {% for t in treinos %}
        <div style="background:#1e1e1e;padding:12px;border-radius:8px;margin-bottom:10px;">
          <h3>{{ t.nome }}</h3>
          <p>Séries: {{ t.series }} — Repetições: {{ t.repeticoes }}</p>
          <p>{{ t.observacoes }}</p>
          <p><a href="{{ url_for('editar', id=t.id) }}">Editar</a> |
             <a href="{{ url_for('excluir', id=t.id) }}" onclick="return confirm('Excluir exercício?')">Excluir</a></p>
          <h4>Histórico</h4>
          {% if t.historico %}
            <ul>
              {% for h in t.historico|reverse %}
                <li>{{ h.data }} — Peso: {{ h.peso }} — Reps: {{ h.reps }}</li>
              {% endfor %}
            </ul>
          {% else %}
            <p>Nenhum histórico.</p>
          {% endif %}
        </div>
      {% endfor %}
    {% else %}
      <p>Nenhum treino cadastrado.</p>
    {% endif %}
  </section>
</body>
</html>
"""

ADMIN_DASH_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Admin - Dashboard</title></head>
<body style="font-family:Arial;padding:20px;">
  <h1>Dashboard Administrativo</h1>
  <ul>
    <li>Total de usuários: {{ total }}</li>
    <li>Usuários ativos: {{ ativos }}</li>
    <li>Usuários bloqueados: {{ bloqueados }}</li>
    <li>Total de treinos: {{ total_treinos }}</li>
  </ul>

  <h2>Últimos registros</h2>
  <ul>
    {% for login, meta in recent_regs %}
      <li>{{ login }} — {{ meta.data_cadastro }}</li>
    {% endfor %}
  </ul>

  <h2>Últimos acessos</h2>
  <ul>
    {% for login, meta in recent_access %}
      <li>{{ login }} — {{ meta.ultimo_acesso or "-" }}</li>
    {% endfor %}
  </ul>

  <p><a href="{{ url_for('admin_usuarios') }}">Gerenciar Usuários</a></p>
  <p><a href="{{ url_for('index') }}">Voltar ao app</a></p>
</body>
</html>
"""

ADMIN_USERS_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Admin - Usuários</title></head>
<body style="font-family:Arial;padding:20px;">
  <h1>Gerenciar Usuários</h1>

  <form method="get" action="{{ url_for('admin_usuarios') }}">
    <input name="q" placeholder="Pesquisar por login, nome ou sobrenome" value="{{ query }}" style="width:300px;">
    <button type="submit">Pesquisar</button>
    <a href="{{ url_for('admin_usuarios') }}" style="margin-left:10px;">Limpar</a>
  </form>

  <table border="1" cellpadding="6" style="border-collapse:collapse;margin-top:10px;">
    <thead>
      <tr>
        <th>Usuário</th><th>Nome</th><th>Sobrenome</th><th>Tipo</th><th>Status</th><th>Cadastro</th><th>Último acesso</th><th>Ações</th>
      </tr>
    </thead>
    <tbody>
      {% for login, meta in users %}
      <tr>
        <td>{{ login }}</td>
        <td>{{ meta.nome }}</td>
        <td>{{ meta.sobrenome }}</td>
        <td>{{ meta.tipo }}</td>
        <td>{{ 'Ativo' if meta.ativo else 'Bloqueado' }}</td>
        <td>{{ meta.data_cadastro }}</td>
        <td>{{ meta.ultimo_acesso or '-' }}</td>
        <td>
          <a href="{{ url_for('admin_ver_treinos', login=login) }}">Ver treinos</a> |
          <a href="{{ url_for('admin_editar_usuario', login=login) }}">Editar</a> |
          {% if meta.ativo %}
            <form style="display:inline" method="post" action="{{ url_for('admin_bloquear', login=login) }}"><button type="submit">Bloquear</button></form>
          {% else %}
            <form style="display:inline" method="post" action="{{ url_for('admin_desbloquear', login=login) }}"><button type="submit">Desbloquear</button></form>
          {% endif %}
          {% if login != ADMIN_LOGIN %}
            <form style="display:inline" method="post" action="{{ url_for('admin_excluir', login=login) }}" onsubmit="return confirm('Confirma exclusão de ' + '{{login}}' + ' ?');">
              <button type="submit">Excluir</button>
            </form>
          {% endif %}
          <form style="display:inline" method="post" action="{{ url_for('admin_reset_senha', login=login) }}">
            <input type="password" name="nova_senha" placeholder="Nova senha">
            <button type="submit">Resetar</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <p><a href="{{ url_for('admin_dashboard') }}">Voltar ao Dashboard</a></p>
</body>
</html>
"""

ADMIN_EDIT_USER_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Editar Usuário</title></head>
<body style="font-family:Arial;padding:20px;">
  <h1>Editar Usuário: {{ login }}</h1>
  {% if mensagem %}
    <div style="background:#fdd;padding:8px;margin-bottom:10px;">{{ mensagem }}</div>
  {% endif %}
  <form method="post" action="{{ url_for('admin_editar_usuario', login=login) }}">
    <label>Login: <input name="login" value="{{ login }}" required></label><br><br>
    <label>Nome: <input name="nome" value="{{ meta.nome }}" required></label><br><br>
    <label>Sobrenome: <input name="sobrenome" value="{{ meta.sobrenome }}" required></label><br><br>
    <label>Tipo:
      <select name="tipo">
        <option value="usuario" {% if meta.tipo=='usuario' %}selected{% endif %}>Usuário</option>
        <option value="admin" {% if meta.tipo=='admin' %}selected{% endif %}>Administrador</option>
      </select>
    </label><br><br>
    <label>Ativo: <input type="checkbox" name="ativo" {% if meta.ativo %}checked{% endif %}></label><br><br>
    <label>Nova senha (opcional): <input type="password" name="nova_senha"></label><br><br>
    <button type="submit">Salvar</button>
  </form>
  <p><a href="{{ url_for('admin_usuarios') }}">Voltar</a></p>
</body>
</html>
"""

VIEW_TRAINING_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Treinos de {{ login }}</title></head>
<body style="font-family:Arial;padding:20px;">
  <h1>Treinos de {{ login }}</h1>
  <p><a href="{{ url_for('admin_usuarios') }}">Voltar</a></p>

  <h2>Abas</h2>
  {% if dados.abas %}
    <ul>
      {% for aba in dados.abas %}
        <li>{{ aba.id }} — {{ aba.nome }}</li>
      {% endfor %}
    </ul>
  {% else %}
    <p>Nenhuma aba.</p>
  {% endif %}

  <h2>Treinos</h2>
  <p><a href="{{ url_for('admin_criar_treino', login=login) }}">Criar novo treino</a></p>
  {% if dados.treinos %}
    {% for t in dados.treinos %}
      <div style="border:1px solid #ccc;padding:8px;margin:8px 0;">
        <strong>{{ t.nome }}</strong> (id: {{ t.id }})<br>
        Séries: {{ t.series }} — Reps: {{ t.repeticoes }}<br>
        Observações: {{ t.observacoes }}<br>
        <a href="{{ url_for('admin_editar_treino', login=login, treino_id=t.id) }}">Editar</a> |
        <a href="{{ url_for('admin_excluir_treino', login=login, treino_id=t.id) }}" onclick="return confirm('Excluir treino?')">Excluir</a> |
        <a href="{{ url_for('admin_duplicar_treino', login=login, treino_id=t.id) }}">Duplicar</a>
        <h4>Histórico</h4>
        {% if t.historico %}
          <ul>
            {% for h in t.historico %}
              <li>{{ h.data }} — peso {{ h.peso }} — reps {{ h.reps }}</li>
            {% endfor %}
          </ul>
        {% else %}
          <p>Sem histórico</p>
        {% endif %}
      </div>
    {% endfor %}
  {% else %}
    <p>Nenhum treino.</p>
  {% endif %}
</body>
</html>
"""

ADMIN_EDIT_TREINO_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Editar Treino</title></head>
<body style="font-family:Arial;padding:20px;">
  <h1>{{ 'Editar' if treino else 'Criar' }} Treino para {{ login }}</h1>
  <form method="post" action="">
    <label>Nome: <input name="nome" value="{{ treino.nome if treino else '' }}" required></label><br><br>
    <label>Aba ID: <input name="aba_id" value="{{ treino.aba_id if treino else '' }}"></label><br><br>
    <label>Séries: <input name="series" value="{{ treino.series if treino else '' }}"></label><br><br>
    <label>Repetições: <input name="repeticoes" value="{{ treino.repeticoes if treino else '' }}"></label><br><br>
    <label>Observações:<br><textarea name="observacoes" rows="4" cols="60">{{ treino.observacoes if treino else '' }}</textarea></label><br><br>
    <button type="submit">Salvar</button>
  </form>
  <p><a href="{{ url_for('admin_ver_treinos', login=login) }}">Voltar</a></p>
</body>
</html>
"""

# ----------------------------
# Rotas de autenticação
# ----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        users = carregar_usuarios()
        if usuario not in users:
            return render_template_string(LOGIN_HTML, mensagem="Usuário não encontrado")
        u = users[usuario]
        if not u.get("ativo", True):
            return render_template_string(LOGIN_HTML, mensagem="Usuário bloqueado. Entre em contato com o administrador.")
        if not check_password_hash(u["senha"], senha):
            return render_template_string(LOGIN_HTML, mensagem="Senha incorreta")
        # login ok
        session["usuario"] = usuario
        users[usuario]["ultimo_acesso"] = now_iso()
        salvar_usuarios(users)
        if users[usuario].get("tipo") == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("index"))
    return render_template_string(LOGIN_HTML)

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        sobrenome = request.form.get("sobrenome", "").strip()
        senha = request.form.get("senha", "")
        confirmar = request.form.get("confirmar_senha", "")
        if not nome or not sobrenome:
            return render_template_string(REGISTRO_HTML, mensagem="Nome e sobrenome são obrigatórios")
        if senha != confirmar:
            return render_template_string(REGISTRO_HTML, mensagem="Senhas não conferem")
        login_name = f"{nome}.{sobrenome}".lower().replace(" ", "")
        users = carregar_usuarios()
        if login_name in users:
            return render_template_string(REGISTRO_HTML, mensagem="Este usuário já existe")
        users[login_name] = {
            "nome": nome,
            "sobrenome": sobrenome,
            "senha": generate_password_hash(senha),
            "tipo": "usuario",
            "ativo": True,
            "data_cadastro": now_iso(),
            "ultimo_acesso": None
        }
        salvar_usuarios(users)
        salvar_dados_usuario(login_name, {"abas": [], "treinos": []})
        return render_template_string(REGISTRO_HTML, mensagem=f"Conta criada com sucesso! Usuário: {login_name}")
    return render_template_string(REGISTRO_HTML)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ----------------------------
# Rotas da aplicação principal (usuário comum)
# ----------------------------
@app.route("/")
def index():
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    dados = carregar_dados_usuario(usuario)
    aba_id = request.args.get("aba")
    treinos = dados.get("treinos", [])
    if aba_id:
        treinos = [t for t in treinos if str(t.get("aba_id")) == str(aba_id)]
    users = carregar_usuarios()
    is_admin = users.get(usuario, {}).get("tipo") == "admin"
    return render_template_string(MAIN_HTML, usuario=usuario, abas=dados.get("abas", []), treinos=treinos, mensagem=request.args.get("mensagem"), is_admin=is_admin)

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
    if "arquivo" not in request.files:
        return redirect(url_for("index", mensagem="Nenhum arquivo selecionado", tipo="erro"))
    arquivo = request.files["arquivo"]
    if arquivo.filename == "":
        return redirect(url_for("index", mensagem="Nenhum arquivo selecionado", tipo="erro"))
    try:
        conteudo = json.loads(arquivo.read().decode("utf-8"))
    except Exception:
        return redirect(url_for("index", mensagem="Arquivo JSON inválido", tipo="erro"))
    if "abas" not in conteudo or "treinos" not in conteudo:
        return redirect(url_for("index", mensagem="Estrutura inválida", tipo="erro"))
    salvar_dados_usuario(usuario, conteudo)
    return redirect(url_for("index", mensagem="Dados importados com sucesso!", tipo="sucesso"))

@app.route("/criar_aba", methods=["POST"])
def criar_aba():
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    dados = carregar_dados_usuario(usuario)
    novo_id = 1
    if dados.get("abas"):
        novo_id = max((a.get("id", 0) for a in dados["abas"]), default=0) + 1
    nova = {"id": novo_id, "nome": request.form.get("nome", "")}
    dados.setdefault("abas", []).append(nova)
    salvar_dados_usuario(usuario, dados)
    return redirect(url_for("index"))

@app.route("/editar_aba/<int:id>", methods=["GET", "POST"])
def editar_aba(id):
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    dados = carregar_dados_usuario(usuario)
    aba = next((a for a in dados.get("abas", []) if a.get("id") == id), None)
    if not aba:
        return "Aba não encontrada", 404
    if request.method == "POST":
        aba["nome"] = request.form.get("nome", aba.get("nome"))
        salvar_dados_usuario(usuario, dados)
        return redirect(url_for("index"))
    return f"""
    <body style="font-family:Arial;padding:20px;">
      <h1>Editar Aba</h1>
      <form method="post">
        <input name="nome" value="{aba.get('nome','')}" required>
        <button type="submit">Salvar</button>
      </form>
    </body>
    """

@app.route("/excluir_aba/<int:id>")
def excluir_aba(id):
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    dados = carregar_dados_usuario(usuario)
    dados["abas"] = [a for a in dados.get("abas", []) if a.get("id") != id]
    dados["treinos"] = [t for t in dados.get("treinos", []) if t.get("aba_id") != id]
    salvar_dados_usuario(usuario, dados)
    return redirect(url_for("index"))

@app.route("/adicionar", methods=["POST"])
def adicionar():
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    dados = carregar_dados_usuario(usuario)
    novo_id = 1
    if dados.get("treinos"):
        novo_id = max((t.get("id", 0) for t in dados["treinos"]), default=0) + 1
    novo = {
        "id": novo_id,
        "aba_id": int(request.form.get("aba_id") or 0),
        "nome": request.form.get("nome", ""),
        "imagem": request.form.get("imagem", ""),
        "series": request.form.get("series", ""),
        "repeticoes": request.form.get("repeticoes", ""),
        "observacoes": request.form.get("observacoes", ""),
        "historico": []
    }
    dados.setdefault("treinos", []).append(novo)
    salvar_dados_usuario(usuario, dados)
    return redirect(url_for("index"))

@app.route("/registrar/<int:id>", methods=["POST"])
def registrar_treino(id):
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    dados = carregar_dados_usuario(usuario)
    for t in dados.get("treinos", []):
        if t.get("id") == id:
            t.setdefault("historico", []).append({
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "peso": request.form.get("peso"),
                "reps": request.form.get("reps")
            })
            break
    salvar_dados_usuario(usuario, dados)
    return redirect(url_for("index"))

@app.route("/excluir/<int:id>")
def excluir(id):
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    dados = carregar_dados_usuario(usuario)
    dados["treinos"] = [t for t in dados.get("treinos", []) if t.get("id") != id]
    salvar_dados_usuario(usuario, dados)
    return redirect(url_for("index"))

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    dados = carregar_dados_usuario(usuario)
    treino = next((t for t in dados.get("treinos", []) if t.get("id") == id), None)
    if not treino:
        return "Treino não encontrado", 404
    if request.method == "POST":
        treino["nome"] = request.form.get("nome", treino.get("nome"))
        treino["imagem"] = request.form.get("imagem", treino.get("imagem"))
        treino["series"] = request.form.get("series", treino.get("series"))
        treino["repeticoes"] = request.form.get("repeticoes", treino.get("repeticoes"))
        treino["observacoes"] = request.form.get("observacoes", treino.get("observacoes"))
        salvar_dados_usuario(usuario, dados)
        return redirect(url_for("index"))
    return f"""
    <body style="font-family:Arial;padding:20px;">
      <h1>Editar Exercício</h1>
      <form method="post">
        <input name="nome" value="{treino.get('nome','')}" required><br><br>
        <input name="imagem" value="{treino.get('imagem','')}"><br><br>
        <input name="series" value="{treino.get('series','')}"><br><br>
        <input name="repeticoes" value="{treino.get('repeticoes','')}"><br><br>
        <textarea name="observacoes">{treino.get('observacoes','')}</textarea><br><br>
        <button type="submit">Salvar</button>
      </form>
    </body>
    """

# ----------------------------
# Rotas administrativas
# ----------------------------
@app.route("/admin")
@admin_required
def admin_dashboard():
    users = carregar_usuarios()
    total = len(users)
    ativos = sum(1 for u in users.values() if u.get("ativo", True))
    bloqueados = total - ativos
    total_treinos = 0
    for login in users.keys():
        dados = carregar_dados_usuario(login)
        total_treinos += len(dados.get("treinos", []))
    recent_regs = sorted(users.items(), key=lambda kv: kv[1].get("data_cadastro",""), reverse=True)[:5]
    recent_access = sorted(users.items(), key=lambda kv: kv[1].get("ultimo_acesso") or "", reverse=True)[:5]
    return render_template_string(ADMIN_DASH_HTML, total=total, ativos=ativos, bloqueados=bloqueados, total_treinos=total_treinos, recent_regs=recent_regs, recent_access=recent_access)

@app.route("/admin/usuarios")
@admin_required
def admin_usuarios():
    q = (request.args.get("q") or "").strip().lower()
    users = carregar_usuarios()
    items = []
    for login, meta in users.items():
        if q:
            if q not in login.lower() and q not in meta.get("nome","").lower() and q not in meta.get("sobrenome","").lower():
                continue
        items.append((login, meta))
    items_sorted = sorted(items, key=lambda kv: kv[0].lower())
    return render_template_string(ADMIN_USERS_HTML, users=items_sorted, query=q, ADMIN_LOGIN=ADMIN_LOGIN)

@app.route("/admin/usuario/editar/<login>", methods=["GET", "POST"])
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
        nova_senha = request.form.get("nova_senha", "").strip()

        # Security invariants: ADMIN_LOGIN cannot be demoted/blocked/excluded
        if login == ADMIN_LOGIN:
            tipo = "admin"
            ativo = True
        if session.get("usuario") == login and tipo != "admin":
            # cannot demote yourself if you're admin
            tipo = "admin"

        # Validate fields
        if not novo_login:
            return render_template_string(ADMIN_EDIT_USER_HTML, login=login, meta=meta, mensagem="Login inválido")
        if not nome or not sobrenome:
            return render_template_string(ADMIN_EDIT_USER_HTML, login=login, meta=meta, mensagem="Nome/sobrenome inválidos")

        # Rename logic
        users = carregar_usuarios()  # reload to avoid stale
        meta = users.pop(login)
        meta["nome"] = nome
        meta["sobrenome"] = sobrenome
        meta["tipo"] = tipo
        meta["ativo"] = bool(ativo)
        if nova_senha:
            meta["senha"] = generate_password_hash(nova_senha)

        # if changing login key
        if novo_login != login:
            # prevent collision
            if novo_login in users:
                # put back old and fail
                users[login] = meta
                salvar_usuarios(users)
                return render_template_string(ADMIN_EDIT_USER_HTML, login=login, meta=meta, mensagem="Novo login já existe")
            # rename file
            old_path = user_data_path(login)
            new_path = user_data_path(novo_login)
            if os.path.exists(old_path):
                os.replace(old_path, new_path)
            users[novo_login] = meta
        else:
            users[login] = meta

        salvar_usuarios(users)
        return redirect(url_for("admin_usuarios"))

    return render_template_string(ADMIN_EDIT_USER_HTML, login=login, meta=meta)

@app.route("/admin/usuario/reset_senha/<login>", methods=["POST"])
@admin_required
def admin_reset_senha(login):
    if login == ADMIN_LOGIN:
        return "Não é permitido alterar a senha do admin por aqui.", 403
    nova = (request.form.get("nova_senha") or "").strip()
    if not nova:
        return redirect(url_for("admin_usuarios"))
    users = carregar_usuarios()
    if login not in users:
        return "Usuário não encontrado", 404
    users[login]["senha"] = generate_password_hash(nova)
    salvar_usuarios(users)
    return redirect(url_for("admin_usuarios"))

@app.route("/admin/usuario/bloquear/<login>", methods=["POST"])
@admin_required
def admin_bloquear(login):
    if login == ADMIN_LOGIN:
        return "Não é permitido bloquear o admin.", 403
    users = carregar_usuarios()
    if login not in users:
        return "Usuário não encontrado", 404
    users[login]["ativo"] = False
    salvar_usuarios(users)
    return redirect(url_for("admin_usuarios"))

@app.route("/admin/usuario/desbloquear/<login>", methods=["POST"])
@admin_required
def admin_desbloquear(login):
    users = carregar_usuarios()
    if login not in users:
        return "Usuário não encontrado", 404
    users[login]["ativo"] = True
    salvar_usuarios(users)
    return redirect(url_for("admin_usuarios"))

@app.route("/admin/usuario/excluir/<login>", methods=["POST"])
@admin_required
def admin_excluir(login):
    if login == ADMIN_LOGIN:
        return "Não é permitido excluir o admin.", 403
    users = carregar_usuarios()
    if login not in users:
        return "Usuário não encontrado", 404
    # remove key and file
    users.pop(login)
    salvar_usuarios(users)
    p = user_data_path(login)
    if os.path.exists(p):
        os.remove(p)
    return redirect(url_for("admin_usuarios"))

@app.route("/admin/usuario/treinos/<login>")
@admin_required
def admin_ver_treinos(login):
    users = carregar_usuarios()
    if login not in users:
        return "Usuário não encontrado", 404
    dados = carregar_dados_usuario(login)
    return render_template_string(VIEW_TRAINING_HTML, login=login, dados=dados)

# Admin: criar/editar/excluir/duplicar treinos de um usuário
@app.route("/admin/usuario/<login>/treino/criar", methods=["GET", "POST"])
@admin_required
def admin_criar_treino(login):
    users = carregar_usuarios()
    if login not in users:
        return "Usuário não encontrado", 404
    if request.method == "POST":
        dados = carregar_dados_usuario(login)
        novo_id = 1
        if dados.get("treinos"):
            novo_id = max((t.get("id",0) for t in dados["treinos"]), default=0) + 1
        treino = {
            "id": novo_id,
            "aba_id": int(request.form.get("aba_id") or 0),
            "nome": request.form.get("nome",""),
            "imagem": "",
            "series": request.form.get("series",""),
            "repeticoes": request.form.get("repeticoes",""),
            "observacoes": request.form.get("observacoes",""),
            "historico": []
        }
        dados.setdefault("treinos", []).append(treino)
        salvar_dados_usuario(login, dados)
        return redirect(url_for("admin_ver_treinos", login=login))
    return render_template_string(ADMIN_EDIT_TREINO_HTML, login=login, treino=None)

@app.route("/admin/usuario/<login>/treino/<int:treino_id>/editar", methods=["GET", "POST"])
@admin_required
def admin_editar_treino(login, treino_id):
    users = carregar_usuarios()
    if login not in users:
        return "Usuário não encontrado", 404
    dados = carregar_dados_usuario(login)
    treino = next((t for t in dados.get("treinos", []) if t.get("id") == treino_id), None)
    if not treino:
        return "Treino não encontrado", 404
    if request.method == "POST":
        treino["nome"] = request.form.get("nome", treino.get("nome"))
        treino["aba_id"] = int(request.form.get("aba_id") or treino.get("aba_id",0))
        treino["series"] = request.form.get("series", treino.get("series"))
        treino["repeticoes"] = request.form.get("repeticoes", treino.get("repeticoes"))
        treino["observacoes"] = request.form.get("observacoes", treino.get("observacoes"))
        salvar_dados_usuario(login, dados)
        return redirect(url_for("admin_ver_treinos", login=login))
    return render_template_string(ADMIN_EDIT_TREINO_HTML, login=login, treino=treino)

@app.route("/admin/usuario/<login>/treino/<int:treino_id>/excluir")
@admin_required
def admin_excluir_treino(login, treino_id):
    users = carregar_usuarios()
    if login not in users:
        return "Usuário não encontrado", 404
    dados = carregar_dados_usuario(login)
    dados["treinos"] = [t for t in dados.get("treinos", []) if t.get("id") != treino_id]
    salvar_dados_usuario(login, dados)
    return redirect(url_for("admin_ver_treinos", login=login))

@app.route("/admin/usuario/<login>/treino/<int:treino_id>/duplicar")
@admin_required
def admin_duplicar_treino(login, treino_id):
    users = carregar_usuarios()
    if login not in users:
        return "Usuário não encontrado", 404
    dados = carregar_dados_usuario(login)
    treino = next((t for t in dados.get("treinos", []) if t.get("id") == treino_id), None)
    if not treino:
        return "Treino não encontrado", 404
    novo_id = max((t.get("id",0) for t in dados.get("treinos",[])), default=0) + 1
    novo = json.loads(json.dumps(treino))  # deep copy
    novo["id"] = novo_id
    novo["nome"] = f"{novo.get('nome','')}_copy"
    dados.setdefault("treinos", []).append(novo)
    salvar_dados_usuario(login, dados)
    return redirect(url_for("admin_ver_treinos", login=login))

# ----------------------------
# Inicialização
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
