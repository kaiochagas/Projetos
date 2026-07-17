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

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Meu Treino</title>
<style>
body{
   background:#121212;
   color:white;
   font-family:Arial;
   margin:20px;
}
h1{
   text-align:center;
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
   width:100%;
   padding:12px;
   margin-top:10px;
   border:none;
   border-radius:10px;
   color:white;
   font-size:16px;
   cursor:pointer;
}
.salvar{
   background:#00b894;
}
.editar{
   background:#0984e3;
}
.excluir{
   background:#d63031;
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
</style>
</head>
<body>
<h1>🏋️ Meu Treino</h1>
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
       placeholder="Peso levantado"
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

# Iniciar sistema
if __name__ == "__main__":
   app.run(
       host="0.0.0.0",
       port=5000,
       debug=True
   )
