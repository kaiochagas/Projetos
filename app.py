from flask import Flask, render_template_string, request, redirect, send_file, jsonify, session
import json
import os
from datetime import datetime
from io import BytesIO
import requests
import base64
import hashlib

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sua-chave-secreta-aqui')

# Configurações do GitHub
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'kaiochagas/Projetos')
ARQUIVO_USUARIOS = "usuarios.json"
BRANCH = "main"

def carregar_usuarios():
    """Carregar lista de usuários do GitHub"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ARQUIVO_USUARIOS}?ref={BRANCH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            conteudo = json.loads(base64.b64decode(response.json()['content']))
            return conteudo, response.json()['sha']
        else:
            return {"admin": {"senha_hash": hashlib.sha256("admin123".encode()).hexdigest(), "eh_admin": True}, "usuarios": []}, None
    except Exception as e:
        print(f"Erro ao carregar usuários: {e}")
        return {"admin": {"senha_hash": hashlib.sha256("admin123".encode()).hexdigest(), "eh_admin": True}, "usuarios": []}, None

def salvar_usuarios(dados, sha=None):
    """Salvar usuários no GitHub"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ARQUIVO_USUARIOS}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        
        conteudo_json = json.dumps(dados, ensure_ascii=False, indent=4)
        conteudo_encoded = base64.b64encode(conteudo_json.encode()).decode()
        
        payload = {
            "message": f"Atualizar usuários - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "content": conteudo_encoded,
            "branch": BRANCH
        }
        
        if sha:
            payload["sha"] = sha
        
        response = requests.put(url, json=payload, headers=headers)
        
        if response.status_code in [201, 200]:
            return response.json()['content']['sha']
        else:
            print(f"Erro ao salvar usuários: {response.text}")
            return None
    except Exception as e:
        print(f"Erro ao salvar usuários: {e}")
        return None

def carregar_dados_usuario(nome_usuario):
    """Carregar treinos do usuário"""
    try:
        arquivo = f"{nome_usuario}.json"
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{arquivo}?ref={BRANCH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            conteudo = json.loads(base64.b64decode(response.json()['content']))
            return conteudo, response.json()['sha']
        else:
            return {"abas": [], "treinos": []}, None
    except Exception as e:
        print(f"Erro ao carregar dados do usuário: {e}")
        return {"abas": [], "treinos": []}, None

def salvar_dados_usuario(nome_usuario, dados, sha=None):
    """Salvar treinos do usuário"""
    try:
        arquivo = f"{nome_usuario}.json"
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{arquivo}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        
        conteudo_json = json.dumps(dados, ensure_ascii=False, indent=4)
        conteudo_encoded = base64.b64encode(conteudo_json.encode()).decode()
        
        payload = {
            "message": f"Atualizar treinos de {nome_usuario} - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "content": conteudo_encoded,
            "branch": BRANCH
        }
        
        if sha:
            payload["sha"] = sha
        
        response = requests.put(url, json=payload, headers=headers)
        
        if response.status_code in [201, 200]:
            return response.json()['content']['sha']
        else:
            print(f"Erro ao salvar dados: {response.text}")
            return None
    except Exception as e:
        print(f"Erro ao salvar dados: {e}")
        return None

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Login - Meu Treino</title>
<style>
* {
   margin: 0;
   padding: 0;
   box-sizing: border-box;
}

body {
   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
   display: flex;
   justify-content: center;
   align-items: center;
   height: 100vh;
   font-family: Arial, sans-serif;
}

.login-container {
   background: white;
   padding: 40px;
   border-radius: 15px;
   box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
   width: 100%;
   max-width: 400px;
}

h1 {
   text-align: center;
   color: #333;
   margin-bottom: 30px;
}

.form-group {
   margin-bottom: 20px;
}

label {
   display: block;
   color: #555;
   margin-bottom: 8px;
   font-weight: bold;
}

input {
   width: 100%;
   padding: 12px;
   border: 2px solid #ddd;
   border-radius: 8px;
   font-size: 16px;
   transition: border-color 0.3s;
}

input:focus {
   outline: none;
   border-color: #667eea;
}

button {
   width: 100%;
   padding: 12px;
   background: #667eea;
   color: white;
   border: none;
   border-radius: 8px;
   font-size: 16px;
   font-weight: bold;
   cursor: pointer;
   transition: background 0.3s;
}

button:hover {
   background: #764ba2;
}

.alert {
   padding: 15px;
   margin-bottom: 20px;
   border-radius: 8px;
   display: none;
}

.alert.erro {
   background: #f8d7da;
   color: #721c24;
   display: block;
}

.alert.sucesso {
   background: #d4edda;
   color: #155724;
   display: block;
}

.links {
   text-align: center;
   margin-top: 20px;
}

.links a {
   color: #667eea;
   text-decoration: none;
   margin: 0 10px;
}

.links a:hover {
   text-decoration: underline;
}

</style>
</head>
<body>
<div class="login-container">
   <h1>🏋️ Meu Treino</h1>
   
   {% if mensagem %}
   <div class="alert {% if tipo_mensagem == 'erro' %}erro{% else %}sucesso{% endif %}">
       {{ mensagem }}
   </div>
   {% endif %}
   
   <form method="POST" action="/login">
       <div class="form-group">
           <label for="usuario">Usuário:</label>
           <input type="text" id="usuario" name="usuario" placeholder="Digite seu usuário" required>
       </div>
       <div class="form-group">
           <label for="senha">Senha:</label>
           <input type="password" id="senha" name="senha" placeholder="Digite sua senha" required>
       </div>
       <button type="submit">Entrar</button>
   </form>
   
   <div class="links">
       <a href="/registro">Criar Conta</a>
   </div>
</div>
</body>
</html>
"""

REGISTRO_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Registro - Meu Treino</title>
<style>
* {
   margin: 0;
   padding: 0;
   box-sizing: border-box;
}

body {
   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
   display: flex;
   justify-content: center;
   align-items: center;
   min-height: 100vh;
   font-family: Arial, sans-serif;
   padding: 20px;
}

.registro-container {
   background: white;
   padding: 40px;
   border-radius: 15px;
   box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
   width: 100%;
   max-width: 400px;
}

h1 {
   text-align: center;
   color: #333;
   margin-bottom: 30px;
}

.form-group {
   margin-bottom: 20px;
}

label {
   display: block;
   color: #555;
   margin-bottom: 8px;
   font-weight: bold;
}

input {
   width: 100%;
   padding: 12px;
   border: 2px solid #ddd;
   border-radius: 8px;
   font-size: 16px;
   transition: border-color 0.3s;
}

input:focus {
   outline: none;
   border-color: #667eea;
}

button {
   width: 100%;
   padding: 12px;
   background: #667eea;
   color: white;
   border: none;
   border-radius: 8px;
   font-size: 16px;
   font-weight: bold;
   cursor: pointer;
   transition: background 0.3s;
}

button:hover {
   background: #764ba2;
}

.alert {
   padding: 15px;
   margin-bottom: 20px;
   border-radius: 8px;
   display: none;
}

.alert.erro {
   background: #f8d7da;
   color: #721c24;
   display: block;
}

.links {
   text-align: center;
   margin-top: 20px;
}

.links a {
   color: #667eea;
   text-decoration: none;
}

.links a:hover {
   text-decoration: underline;
}

.usuario-gerado {
   background: #e7f3ff;
   padding: 12px;
   border-radius: 8px;
   margin-top: 10px;
   color: #004085;
   font-weight: bold;
   text-align: center;
}

</style>
</head>
<body>
<div class="registro-container">
   <h1>📝 Criar Conta</h1>
   
   {% if mensagem %}
   <div class="alert {% if tipo_mensagem == 'erro' %}erro{% else %}sucesso{% endif %}">
       {{ mensagem }}
   </div>
   {% endif %}
   
   <form method="POST" action="/registrar">
       <div class="form-group">
           <label for="nome">Nome:</label>
           <input type="text" id="nome" name="nome" placeholder="ex: Diego" required>
       </div>
       <div class="form-group">
           <label for="sobrenome">Sobrenome:</label>
           <input type="text" id="sobrenome" name="sobrenome" placeholder="ex: Mota" required>
       </div>
       <div class="form-group">
           <label for="senha">Senha:</label>
           <input type="password" id="senha" name="senha" placeholder="Digite uma senha" required>
       </div>
       <div class="form-group">
           <label for="confirmar_senha">Confirmar Senha:</label>
           <input type="password" id="confirmar_senha" name="confirmar_senha" placeholder="Confirme a senha" required>
       </div>
       <div class="usuario-gerado" id="usuario-preview">
           👤 Usuário: <span id="usuario-span">nome.sobrenome</span>
       </div>
       <button type="submit">Criar Conta</button>
   </form>
   
   <div class="links">
       <a href="/login">Voltar ao Login</a>
   </div>
</div>

<script>
const nomeInput = document.getElementById('nome');
const sobrenomeInput = document.getElementById('sobrenome');
const usuarioSpan = document.getElementById('usuario-span');

function atualizarUsuario() {
    const nome = nomeInput.value.toLowerCase().trim();
    const sobrenome = sobrenomeInput.value.toLowerCase().trim();
    
    if (nome && sobrenome) {
        usuarioSpan.textContent = nome + '.' + sobrenome;
    } else {
        usuarioSpan.textContent = 'nome.sobrenome';
    }
}

nomeInput.addEventListener('input', atualizarUsuario);
sobrenomeInput.addEventListener('input', atualizarUsuario);
</script>
</body>
</html>
"""

HTML_TREINO = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Meu Treino</title>
<style>
* {
   margin: 0;
   padding: 0;
   box-sizing: border-box;
}

body{
   background:#121212;
   color:white;
   font-family:Arial;
   margin:20px;
}

.header {
   display: flex;
   justify-content: space-between;
   align-items: center;
   margin-bottom: 20px;
}

h1{
   text-align:center;
   flex: 1;
}

.user-info {
   display: flex;
   align-items: center;
   gap: 15px;
}

.logout-btn {
   background: #d63031;
   color: white;
   padding: 10px 15px;
   border: none;
   border-radius: 8px;
   cursor: pointer;
   text-decoration: none;
   font-weight: bold;
}

.logout-btn:hover {
   background: #ff6b6b;
}

.card{
   background:#1e1e1e;
   padding:20px;
   border-radius:15px;
   margin-bottom:20px;
}

input, textarea, select{
   width:100%;
   padding:12px;
   margin-top:10px;
   border:none;
   border-radius:10px;
   box-sizing:border-box;
}

textarea{
   resize:none;
   height:100px;
}

button{
   padding:12px;
   border:none;
   border-radius:10px;
   color:white;
   font-size:16px;
   cursor:pointer;
   font-weight: bold;
   transition: transform 0.2s, opacity 0.2s;
}

button:hover{
   transform: translateY(-2px);
   opacity: 0.9;
}

.salvar{
   background:#00b894;
   width:100%;
   margin-top:10px;
}

.editar{
   background:#0984e3;
}

.excluir{
   background:#d63031;
}

.exportar{
   background:#6c5ce7;
}

.importar{
   background:#fd79a8;
}

.aba{
   display:inline-block;
   background:#2d3436;
   padding:10px 15px;
   border-radius:10px;
   margin-right:10px;
   margin-bottom:10px;
}

.aba a{
   color:white;
   text-decoration:none;
}

img{
   width:100%;
   border-radius:15px;
   margin-top:10px;
}

.historico{
   background:#2d3436;
   padding:10px;
   border-radius:10px;
   margin-top:10px;
}

.botoes-container {
   display: flex;
   flex-direction: row;
   gap: 12px;
   margin-top: 15px;
   width: 100%;
}

.botao-grupo {
   flex: 1;
   min-width: 0;
   display: flex;
   align-items: stretch;
}

.botao-grupo form {
   width: 100%;
   display: flex;
   margin: 0;
}

.botao-grupo button,
.botao-grupo label {
   flex: 1;
   display: flex;
   align-items: center;
   justify-content: center;
   height: 50px;
   min-height: 50px;
   padding: 0 15px;
   font-size: 14px;
   font-weight: bold;
   border-radius: 10px;
   border: none;
   cursor: pointer;
   transition: all 0.2s ease;
   white-space: nowrap;
   text-align: center;
}

.botao-grupo button:hover,
.botao-grupo label:hover {
   transform: translateY(-2px);
   opacity: 0.9;
}

input[type="file"]{
   display:none;
}

.label-file {
   display: flex;
   align-items: center;
   justify-content: center;
}

.alert{
   padding:15px;
   margin:10px 0;
   border-radius:10px;
   display:none;
}

.alert.sucesso{
   background:#00b894;
   color:white;
   display:block;
}

.alert.erro{
   background:#d63031;
   color:white;
   display:block;
}

@media (max-width: 768px) {
   .header {
       flex-direction: column;
       gap: 10px;
   }

   .user-info {
       width: 100%;
       justify-content: space-between;
   }

   .botoes-container {
       flex-direction: column;
   }
}

</style>
</head>
<body>

<div class="header">
   <h1>🏋️ Meu Treino</h1>
   <div class="user-info">
       <span>👤 {{ usuario }}</span>
       <a href="/logout" class="logout-btn">Sair</a>
   </div>
</div>

{% if mensagem %}
<div class="alert {% if tipo_mensagem == 'sucesso' %}sucesso{% else %}erro{% endif %}">
   {{ mensagem }}
</div>
{% endif %}

<div class="card">
<h2>⚙️ Gerenciamento de Dados</h2>
<div class="botoes-container">
   <div class="botao-grupo">
       <form action="/exportar" method="GET" style="margin:0; width: 100%;">
           <button class="exportar" type="submit">📤 Exportar Treino</button>
       </form>
   </div>
   <div class="botao-grupo">
       <form action="/importar" method="POST" enctype="multipart/form-data" style="margin:0; width: 100%;">
           <label class="label-file importar" for="arquivo_importar">📥 Importar Treino</label>
           <input type="file" id="arquivo_importar" name="arquivo" accept=".json" onchange="this.form.submit()">
       </form>
   </div>
</div>
</div>

<div class="card">
<h2>➕ Criar Aba</h2>
<form action="/criar_aba" method="POST">
<input
       type="text"
       name="nome"
       placeholder="Ex: Treino A, Perna, Peito..."
       required
>
<button class="salvar" type="submit">
       Criar Aba
</button>
</form>
</div>

<div class="card">
<h2>📂 Abas</h2>
{% if abas %}
   {% for aba in abas %}
<div class="aba">
<a href="/?aba={{ aba.id }}">
       {{ aba.nome }}
</a>
   |
<a href="/editar_aba/{{ aba.id }}">
       ✏️
</a>
   |
<a
       href="/excluir_aba/{{ aba.id }}"
       onclick="return confirm('Excluir aba?')"
>
       🗑️
</a>
</div>
   {% endfor %}
{% else %}
<p style="color: #999;">Nenhuma aba criada. Crie uma para começar!</p>
{% endif %}
</div>

<div class="card">
<h2>➕ Adicionar Exercício</h2>
<form action="/adicionar" method="POST">
<input
       type="text"
       name="nome"
       placeholder="Nome do exercício"
       required
>
<input
       type="text"
       name="imagem"
       placeholder="URL da imagem"
>
<input
       type="text"
       name="series"
       placeholder="Séries"
>
<input
       type="text"
       name="repeticoes"
       placeholder="Repetições"
>
<textarea
       name="observacoes"
       placeholder="Observações"
></textarea>
<select name="aba_id" required>
<option value="">
           Escolha a aba
</option>
       {% for aba in abas %}
<option value="{{ aba.id }}">
           {{ aba.nome }}
</option>
       {% endfor %}
</select>
<button class="salvar" type="submit">
       Adicionar Exercício
</button>
</form>
</div>

{% for treino in treinos %}
<div class="card">
<h2>{{ treino.nome }}</h2>
{% if treino.imagem %}
<img src="{{ treino.imagem }}">
{% endif %}
<p><b>Séries:</b> {{ treino.series }}</p>
<p><b>Repetições:</b> {{ treino.repeticoes }}</p>
<p><b>Observações:</b> {{ treino.observacoes }}</p>
<a href="/editar/{{ treino.id }}">
<button class="editar">
       ✏️ Editar Exercício
</button>
</a>
<a
href="/excluir/{{ treino.id }}"
onclick="return confirm('Excluir exercício?')"
>
<button class="excluir">
       🗑️ Excluir Exercício
</button>
</a>
<form action="/registrar/{{ treino.id }}" method="POST">
<input
       type="text"
       name="peso"
       placeholder="Último Peso levantado"
       required
>
<input
       type="text"
       name="reps"
       placeholder="Repetições atingidas"
       required
>
<button class="salvar" type="submit">
       Salvar Resultado
</button>
</form>
<h3>📈 Histórico</h3>
{% if treino.historico %}
   {% for item in treino.historico[::-1] %}
<div class="historico">
<p><b>Data:</b> {{ item.data }}</p>
<p><b>Peso:</b> {{ item.peso }}</p>
<p><b>Repetições:</b> {{ item.reps }}</p>
</div>
   {% endfor %}
{% else %}
<p>Nenhum histórico ainda.</p>
{% endif %}
</div>
{% endfor %}

</body>
</html>
"""

# ROTAS DE AUTENTICAÇÃO

@app.route("/login", methods=["GET", "POST"])
def login():
   if request.method == "POST":
       usuario = request.form["usuario"]
       senha = request.form["senha"]
       
       usuarios_dados, _ = carregar_usuarios()
       
       if usuario in usuarios_dados:
           usuario_info = usuarios_dados[usuario]
           senha_hash = hashlib.sha256(senha.encode()).hexdigest()
           
           if usuario_info["senha_hash"] == senha_hash:
               session["usuario"] = usuario
               return redirect("/")
           else:
               return render_template_string(LOGIN_HTML, mensagem="Senha incorreta", tipo_mensagem="erro")
       else:
           return render_template_string(LOGIN_HTML, mensagem="Usuário não encontrado", tipo_mensagem="erro")
   
   return render_template_string(LOGIN_HTML)

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
   if request.method == "POST":
       nome = request.form["nome"].strip().lower()
       sobrenome = request.form["sobrenome"].strip().lower()
       senha = request.form["senha"]
       confirmar_senha = request.form["confirmar_senha"]
       
       if not nome or not sobrenome:
           return render_template_string(REGISTRO_HTML, mensagem="Nome e sobrenome são obrigatórios", tipo_mensagem="erro")
       
       if senha != confirmar_senha:
           return render_template_string(REGISTRO_HTML, mensagem="Senhas não conferem", tipo_mensagem="erro")
       
       usuario = f"{nome}.{sobrenome}"
       
       usuarios_dados, sha = carregar_usuarios()
       
       if usuario in usuarios_dados:
           return render_template_string(REGISTRO_HTML, mensagem="Este usuário já existe", tipo_mensagem="erro")
       
       senha_hash = hashlib.sha256(senha.encode()).hexdigest()
       usuarios_dados[usuario] = {"senha_hash": senha_hash, "eh_admin": False}
       
       salvar_usuarios(usuarios_dados, sha)
       
       # Criar arquivo JSON inicial do usuário
       dados_iniciais = {"abas": [], "treinos": []}
       salvar_dados_usuario(usuario, dados_iniciais)
       
       return render_template_string(REGISTRO_HTML, mensagem=f"Conta criada com sucesso! Usuário: {usuario}", tipo_mensagem="sucesso")
   
   return render_template_string(REGISTRO_HTML)

@app.route("/logout")
def logout():
   session.clear()
   return redirect("/login")

# ROTAS PRINCIPAIS

@app.route("/")
def index():
   if "usuario" not in session:
       return redirect("/login")
   
   usuario = session["usuario"]
   dados, sha = carregar_dados_usuario(usuario)
   aba_id = request.args.get("aba")
   treinos = dados["treinos"]
   mensagem = request.args.get("mensagem", "")
   tipo_mensagem = request.args.get("tipo", "")
   
   if aba_id:
       treinos = [
           treino for treino in treinos
           if str(treino["aba_id"]) == aba_id
       ]
   
   return render_template_string(
       HTML_TREINO,
       abas=dados["abas"],
       treinos=treinos,
       mensagem=mensagem,
       tipo_mensagem=tipo_mensagem,
       usuario=usuario
   )

@app.route("/exportar", methods=["GET"])
def exportar():
   if "usuario" not in session:
       return redirect("/login")
   
   usuario = session["usuario"]
   try:
       dados, _ = carregar_dados_usuario(usuario)
       json_str = json.dumps(dados, ensure_ascii=False, indent=4)
       buffer = BytesIO(json_str.encode('utf-8'))
       return send_file(
           buffer,
           mimetype='application/json',
           as_attachment=True,
           download_name=f'{usuario}_treinos.json'
       )
   except Exception as e:
       return redirect(f"/?mensagem=Erro ao exportar: {str(e)}&tipo=erro")

@app.route("/importar", methods=["POST"])
def importar():
   if "usuario" not in session:
       return redirect("/login")
   
   usuario = session["usuario"]
   try:
       if 'arquivo' not in request.files:
           return redirect("/?mensagem=Nenhum arquivo selecionado&tipo=erro")
       
       arquivo = request.files['arquivo']
       
       if arquivo.filename == '':
           return redirect("/?mensagem=Nenhum arquivo selecionado&tipo=erro")
       
       try:
           conteudo = json.loads(arquivo.read().decode('utf-8'))
       except json.JSONDecodeError:
           return redirect("/?mensagem=Arquivo JSON inválido&tipo=erro")
       
       if 'abas' not in conteudo or 'treinos' not in conteudo:
           return redirect("/?mensagem=Estrutura de JSON inválida&tipo=erro")
       
       _, sha = carregar_dados_usuario(usuario)
       salvar_dados_usuario(usuario, conteudo, sha)
       return redirect("/?mensagem=Dados importados com sucesso!&tipo=sucesso")
       
   except Exception as e:
       return redirect(f"/?mensagem=Erro ao importar: {str(e)}&tipo=erro")

@app.route("/criar_aba", methods=["POST"])
def criar_aba():
   if "usuario" not in session:
       return redirect("/login")
   
   usuario = session["usuario"]
   dados, sha = carregar_dados_usuario(usuario)
   novo_id = 1
   if dados["abas"]:
       novo_id = max(a["id"] for a in dados["abas"]) + 1
   nova_aba = {
       "id": novo_id,
       "nome": request.form["nome"]
   }
   dados["abas"].append(nova_aba)
   salvar_dados_usuario(usuario, dados, sha)
   return redirect("/")

@app.route("/editar_aba/<int:id>", methods=["GET", "POST"])
def editar_aba(id):
   if "usuario" not in session:
       return redirect("/login")
   
   usuario = session["usuario"]
   dados, sha = carregar_dados_usuario(usuario)
   aba = None
   for a in dados["abas"]:
       if a["id"] == id:
           aba = a
           break
   if request.method == "POST":
       aba["nome"] = request.form["nome"]
       salvar_dados_usuario(usuario, dados, sha)
       return redirect("/")
   return f"""
<body style="background:#121212;color:white;font-family:Arial;padding:20px;">
<h1>✏️ Editar Aba</h1>
<form method="POST">
<input
           type="text"
           name="nome"
           value="{aba['nome']}"
           style="width:100%;padding:12px;border:none;border-radius:10px;"
>
<button
           type="submit"
           style="width:100%;padding:12px;margin-top:10px;background:#0984e3;color:white;border:none;border-radius:10px;"
>
           Salvar
</button>
</form>
</body>
   """

@app.route("/excluir_aba/<int:id>")
def excluir_aba(id):
   if "usuario" not in session:
       return redirect("/login")
   
   usuario = session["usuario"]
   dados, sha = carregar_dados_usuario(usuario)
   dados["abas"] = [
       aba for aba in dados["abas"]
       if aba["id"] != id
   ]
   dados["treinos"] = [
       treino for treino in dados["treinos"]
       if treino["aba_id"] != id
   ]
   salvar_dados_usuario(usuario, dados, sha)
   return redirect("/")

@app.route("/adicionar", methods=["POST"])
def adicionar():
   if "usuario" not in session:
       return redirect("/login")
   
   usuario = session["usuario"]
   dados, sha = carregar_dados_usuario(usuario)
   novo_id = 1
   if dados["treinos"]:
       novo_id = max(t["id"] for t in dados["treinos"]) + 1
   novo = {
       "id": novo_id,
       "aba_id": int(request.form["aba_id"]),
       "nome": request.form["nome"],
       "imagem": request.form["imagem"],
       "series": request.form["series"],
       "repeticoes": request.form["repeticoes"],
       "observacoes": request.form["observacoes"],
       "historico": []
   }
   dados["treinos"].append(novo)
   salvar_dados_usuario(usuario, dados, sha)
   return redirect("/?aba=" + request.form["aba_id"])

@app.route("/registrar/<int:id>", methods=["POST"])
def registrar_treino(id):
   if "usuario" not in session:
       return redirect("/login")
   
   usuario = session["usuario"]
   dados, sha = carregar_dados_usuario(usuario)
   for treino in dados["treinos"]:
       if treino["id"] == id:
           treino["historico"].append({
               "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
               "peso": request.form["peso"],
               "reps": request.form["reps"]
           })
           break
   salvar_dados_usuario(usuario, dados, sha)
   return redirect("/")

@app.route("/excluir/<int:id>")
def excluir(id):
   if "usuario" not in session:
       return redirect("/login")
   
   usuario = session["usuario"]
   dados, sha = carregar_dados_usuario(usuario)
   dados["treinos"] = [
       treino for treino in dados["treinos"]
       if treino["id"] != id
   ]
   salvar_dados_usuario(usuario, dados, sha)
   return redirect("/")

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
   if "usuario" not in session:
       return redirect("/login")
   
   usuario = session["usuario"]
   dados, sha = carregar_dados_usuario(usuario)
   treino = None
   for t in dados["treinos"]:
       if t["id"] == id:
           treino = t
           break
   if request.method == "POST":
       treino["nome"] = request.form["nome"]
       treino["imagem"] = request.form["imagem"]
       treino["series"] = request.form["series"]
       treino["repeticoes"] = request.form["repeticoes"]
       treino["observacoes"] = request.form["observacoes"]
       salvar_dados_usuario(usuario, dados, sha)
       return redirect("/")
   return f"""
<body style="background:#121212;color:white;font-family:Arial;padding:20px;">
<h1>✏️ Editar Exercício</h1>
<form method="POST">
<input
           type="text"
           name="nome"
           value="{treino['nome']}"
           style="width:100%;padding:12px;margin-top:10px;border:none;border-radius:10px;"
>
<input
           type="text"
           name="imagem"
           value="{treino['imagem']}"
           style="width:100%;padding:12px;margin-top:10px;border:none;border-radius:10px;"
>
<input
           type="text"
           name="series"
           value="{treino['series']}"
           style="width:100%;padding:12px;margin-top:10px;border:none;border-radius:10px;"
>
<input
           type="text"
           name="repeticoes"
           value="{treino['repeticoes']}"
           style="width:100%;padding:12px;margin-top:10px;border:none;border-radius:10px;"
>
<textarea
           name="observacoes"
           style="width:100%;height:100px;padding:12px;margin-top:10px;border:none;border-radius:10px;"
>{treino['observacoes']}</textarea>
<button
           type="submit"
           style="width:100%;padding:12px;margin-top:10px;background:#0984e3;color:white;border:none;border-radius:10px;"
>
           Salvar
</button>
</form>
</body>
   """

if __name__ == "__main__":
   port = os.environ.get('PORT', 5000)
   app.run(
       host="0.0.0.0",
       port=int(port),
       debug=False
   )
