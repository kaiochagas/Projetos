# app.py
from flask import Flask, render_template_string, request, redirect
import json
import os
from datetime import datetime

app = Flask(__name__)

ARQUIVO_JSON = "treinos.json"

# Criar arquivo inicial
if not os.path.exists(ARQUIVO_JSON):
    dados_iniciais = {
        "abas": [
            {
                "id": 1,
                "nome": "Treino A"
            }
        ],
        "treinos": []
    }
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(dados_iniciais, f, ensure_ascii=False, indent=4)

# Carregar dados
def carregar_dados():
    with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

# Salvar dados
def salvar_dados(dados):
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# Shared head: styles + theme toggle
SHARED_HEAD = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{
  --bg: #121212;
  --card: #1e1e1e;
  --text: #ffffff;
  --accent: #667eea;
  --muted: #9aa0a6;
  --danger: #e74c3c;
}
:root.light{
  --bg: #f5f6fb;
  --card: #ffffff;
  --text: #111827;
  --accent: #4f46e5;
  --muted: #666666;
  --danger: #c0392b;
}
*{box-sizing:border-box}
html,body{height:100%;margin:0;font-family:Inter, system-ui, -apple-system, "Helvetica Neue", Arial;}
body{background:var(--bg);color:var(--text);display:flex;align-items:center;justify-content:center;padding:20px;}
.container{width:100%;max-width:1100px;margin:0 auto}
.center-card{background:var(--card);padding:24px;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.35);}
.header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:18px}
.brand{display:flex;align-items:center;gap:12px}
.logo{font-size:28px;line-height:1;display:flex;align-items:center}
.title{font-weight:800;font-size:20px}
.actions{display:flex;align-items:center;gap:8px}
.form{max-width:900px;margin:0 auto}
.field{margin-bottom:12px}
label{display:block;font-size:14px;color:var(--muted);margin-bottom:6px}
input[type="text"], input[type="password"], textarea, select{
  width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:transparent;color:var(--text)
}
textarea{resize:vertical;min-height:100px}
button.btn{background:var(--accent);color:white;border:none;padding:10px 14px;border-radius:8px;cursor:pointer;font-weight:600}
button.ghost{background:transparent;color:var(--text);border:1px solid rgba(255,255,255,0.06);padding:8px 12px;border-radius:8px;cursor:pointer}
.small{padding:6px 10px;font-size:14px}
.card{background:transparent;padding:20px;border-radius:12px;margin-bottom:20px;border:1px solid rgba(255,255,255,0.03)}
.aba{display:inline-block;background:rgba(255,255,255,0.03);padding:8px 12px;border-radius:8px;margin-right:10px;margin-bottom:10px}
.aba a{color:var(--text);text-decoration:none}
.historico{background:rgba(255,255,255,0.03);padding:12px;border-radius:8px;margin-top:10px}
img{max-width:100%;border-radius:10px;margin-top:10px}
@media (max-width:720px){
  .header{flex-direction:column;align-items:flex-start}
  .title{font-size:18px}
}
</style>

<script>
function initThemeToggle(){
  const root = document.documentElement;
  const stored = localStorage.getItem('theme');
  if(stored === 'light') root.classList.add('light');
  document.addEventListener('click', function(e){
    if(e.target && e.target.matches('[data-toggle-theme]')){
      root.classList.toggle('light');
      localStorage.setItem('theme', root.classList.contains('light') ? 'light' : 'dark');
    }
  });
}
document.addEventListener('DOMContentLoaded', initThemeToggle);
</script>
"""

# Main HTML (updated layout)
HTML = SHARED_HEAD + """

<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Meu Treino</title>
</head>
<body>
<div class="container">
  <div class="center-card">
    <div class="header">
      <div class="brand">
        <div class="logo">🏋️</div>
        <div>
          <div class="title">Meu Treino</div>
          <div style="font-size:13px;color:var(--muted)">Organize seus treinamentos</div>
        </div>
      </div>
      <div class="actions">
        <button class="ghost small" data-toggle-theme>Alternar Tema</button>
      </div>
    </div>

    <div class="card">
      <h2 style="margin-top:0">➕ Criar Aba</h2>
      <form action="/criar_aba" method="POST" class="form">
        <div class="field">
          <label for="nome_aba">Nome da aba</label>
          <input id="nome_aba" type="text" name="nome" placeholder="Ex: Treino A, Perna, Peito..." required>
        </div>
        <div style="display:flex;gap:10px">
          <button class="btn" type="submit">Criar Aba</button>
        </div>
      </form>
    </div>

    <div class="card">
      <h2 style="margin-top:0">📂 Abas</h2>
      {% for aba in abas %}
      <div class="aba">
        <a href="/?aba={{ aba.id }}">{{ aba.nome }}</a> |
        <a href="/editar_aba/{{ aba.id }}">✏️</a> |
        <a href="/excluir_aba/{{ aba.id }}" onclick="return confirm('Excluir aba?')">🗑️</a>
      </div>
      {% endfor %}
    </div>

    <div class="card">
      <h2 style="margin-top:0">➕ Adicionar Exercício</h2>
      <form action="/adicionar" method="POST" class="form">
        <div class="field"><label>Nome do exercício</label><input type="text" name="nome" required></div>
        <div class="field"><label>URL da imagem (opcional)</label><input type="text" name="imagem"></div>
        <div class="field"><label>Séries</label><input type="text" name="series"></div>
        <div class="field"><label>Repetições</label><input type="text" name="repeticoes"></div>
        <div class="field"><label>Observações</label><textarea name="observacoes"></textarea></div>
        <div class="field">
          <label>Escolha a aba</label>
          <select name="aba_id" required>
            <option value="">Escolha a aba</option>
            {% for aba in abas %}
            <option value="{{ aba.id }}">{{ aba.nome }}</option>
            {% endfor %}
          </select>
        </div>
        <div style="display:flex;gap:10px">
          <button class="btn" type="submit">Adicionar Exercício</button>
        </div>
      </form>
    </div>

    {% for treino in treinos %}
    <div class="card">
      <h2 style="margin-top:0">{{ treino.nome }}</h2>
      {% if treino.imagem %}
      <img src="{{ treino.imagem }}" alt="{{ treino.nome }}">
      {% endif %}
      <p><strong>Séries:</strong> {{ treino.series }}</p>
      <p><strong>Repetições:</strong> {{ treino.repeticoes }}</p>
      <p><strong>Observações:</strong> {{ treino.observacoes }}</p>

      <div style="display:flex;gap:10px;margin-top:8px">
        <a href="/editar/{{ treino.id }}"><button class="ghost small">✏️ Editar</button></a>
        <a href="/excluir/{{ treino.id }}" onclick="return confirm('Excluir exercício?')"><button class="ghost small">🗑️ Excluir</button></a>
      </div>

      <form action="/registrar/{{ treino.id }}" method="POST" style="margin-top:12px">
        <div class="field"><label>Último Peso levantado</label><input type="text" name="peso" placeholder="Peso levantado" required></div>
        <div class="field"><label>Repetições atingidas</label><input type="text" name="reps" placeholder="Repetições" required></div>
        <div style="display:flex;gap:10px">
          <button class="btn" type="submit">Salvar Resultado</button>
        </div>
      </form>

      <h3 style="margin-top:12px">📈 Histórico</h3>
      {% if treino.historico %}
        {% for item in treino.historico[::-1] %}
        <div class="historico">
          <p><b>Data:</b> {{ item.data }}</p>
          <p><b>Peso:</b> {{ item.peso }}</p>
          <p><b>Repetições:</b> {{ item.reps }}</p>
        </div>
        {% endfor %}
      {% else %}
        <p style="color:var(--muted)">Nenhum histórico ainda.</p>
      {% endif %}
    </div>
    {% endfor %}

  </div>
</div>
</body>
</html>
"""

@app.route("/")
def index():
    dados = carregar_dados()
    aba_id = request.args.get("aba")
    treinos = dados["treinos"]
    if aba_id:
        treinos = [
            treino for treino in treinos
            if str(treino["aba_id"]) == aba_id
        ]
    return render_template_string(
        HTML,
        abas=dados["abas"],
        treinos=treinos
    )

# Criar aba
@app.route("/criar_aba", methods=["POST"])
def criar_aba():
    dados = carregar_dados()
    novo_id = 1
    if dados["abas"]:
        novo_id = max(a["id"] for a in dados["abas"]) + 1
    nova_aba = {
        "id": novo_id,
        "nome": request.form["nome"]
    }
    dados["abas"].append(nova_aba)
    salvar_dados(dados)
    return redirect("/")

# Editar aba
@app.route("/editar_aba/<int:id>", methods=["GET", "POST"])
def editar_aba(id):
    dados = carregar_dados()
    aba = None
    for a in dados["abas"]:
        if a["id"] == id:
            aba = a
            break
    if request.method == "POST":
        aba["nome"] = request.form["nome"]
        salvar_dados(dados)
        return redirect("/")
    return f"""
    <body style="background:var(--bg);color:var(--text);font-family:Arial;padding:20px;">
    <h1>✏️ Editar Aba</h1>
    <form method="POST">
        <input type="text" name="nome" value="{aba['nome']}" style="width:100%;padding:12px;border:none;border-radius:10px;">
        <button type="submit" style="width:100%;padding:12px;margin-top:10px;background:#0984e3;color:white;border:none;border-radius:10px;">Salvar</button>
    </form>
    </body>
    """

# Excluir aba
@app.route("/excluir_aba/<int:id>")
def excluir_aba(id):
    dados = carregar_dados()
    dados["abas"] = [
        aba for aba in dados["abas"]
        if aba["id"] != id
    ]
    dados["treinos"] = [
        treino for treino in dados["treinos"]
        if treino["aba_id"] != id
    ]
    salvar_dados(dados)
    return redirect("/")

# Adicionar exercício
@app.route("/adicionar", methods=["POST"])
def adicionar():
    dados = carregar_dados()
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
    salvar_dados(dados)
    return redirect("/?aba=" + request.form["aba_id"])

# Registrar treino
@app.route("/registrar/<int:id>", methods=["POST"])
def registrar(id):
    dados = carregar_dados()
    for treino in dados["treinos"]:
        if treino["id"] == id:
            treino["historico"].append({
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "peso": request.form["peso"],
                "reps": request.form["reps"]
            })
            break
    salvar_dados(dados)
    return redirect("/")

# Excluir exercício
@app.route("/excluir/<int:id>")
def excluir(id):
    dados = carregar_dados()
    dados["treinos"] = [
        treino for treino in dados["treinos"]
        if treino["id"] != id
    ]
    salvar_dados(dados)
    return redirect("/")

# Editar exercício
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    dados = carregar_dados()
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
        salvar_dados(dados)
        return redirect("/")
    return f"""
    <body style="background:var(--bg);color:var(--text);font-family:Arial;padding:20px;">
    <h1>✏️ Editar Exercício</h1>
    <form method="POST">
        <input type="text" name="nome" value="{treino['nome']}" style="width:100%;padding:12px;margin-top:10px;border:none;border-radius:10px;">
        <input type="text" name="imagem" value="{treino['imagem']}" style="width:100%;padding:12px;margin-top:10px;border:none;border-radius:10px;">
        <input type="text" name="series" value="{treino['series']}" style="width:100%;padding:12px;margin-top:10px;border:none;border-radius:10px;">
        <input type="text" name="repeticoes" value="{treino['repeticoes']}" style="width:100%;padding:12px;margin-top:10px;border:none;border-radius:10px;">
        <textarea name="observacoes" style="width:100%;height:100px;padding:12px;margin-top:10px;border:none;border-radius:10px;">{treino['observacoes']}</textarea>
        <button type="submit" style="width:100%;padding:12px;margin-top:10px;background:#0984e3;color:white;border:none;border-radius:10px;">Salvar</button>
    </form>
    </body>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
