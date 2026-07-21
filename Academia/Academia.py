from flask import Flask, render_template_string, request, redirect, send_file, jsonify
import json
import os
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
ARQUIVO_JSON = "treinos.json"

# Criar arquivo inicial
if not os.path.exists(ARQUIVO_JSON):
   dados_iniciais = {
       "abas": [],
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
.mesclar{
   background:#fdcb6e;
   color:#000;
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

/* NOVO: Container responsivo para botões */
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

/* Media Queries Responsivas */
@media (max-width: 1024px) {
   .botoes-container {
       gap: 10px;
   }
   
   .botao-grupo button,
   .botao-grupo label {
       height: 48px;
       min-height: 48px;
       font-size: 14px;
       padding: 0 10px;
   }
}

@media (max-width: 768px) {
   body {
       margin: 15px;
   }
   
   .card {
       padding: 15px;
       margin-bottom: 15px;
   }
   
   .botoes-container {
       flex-direction: row;
       gap: 8px;
   }
   
   .botao-grupo button,
   .botao-grupo label {
       height: 46px;
       min-height: 46px;
       font-size: 13px;
       padding: 0 8px;
   }
}

@media (max-width: 480px) {
   body {
       margin: 10px;
   }
   
   .card {
       padding: 12px;
   }
   
   .botoes-container {
       flex-direction: column;
       gap: 10px;
   }
   
   .botao-grupo {
       width: 100%;
   }
   
   .botao-grupo button,
   .botao-grupo label {
       height: 50px;
       min-height: 50px;
       font-size: 14px;
       padding: 0 12px;
   }
   
   input, textarea, select {
       font-size: 16px;
   }
}

</style>
</head>
<body>
{% if mensagem %}
<div class="alert {% if tipo_mensagem == 'sucesso' %}sucesso{% else %}erro{% endif %}">
   {{ mensagem }}
</div>
{% endif %}

<h1>🏋️ Meu Treino</h1>

<div class="card">
<h2>⚙️ Gerenciamento de Dados</h2>
<div class="botoes-container">
   <div class="botao-grupo">
       <form action="/exportar" method="GET" style="margin:0; width: 100%;">
           <button class="exportar" type="submit">📤 Exportar JSON</button>
       </form>
   </div>
   <div class="botao-grupo">
       <form action="/importar" method="POST" enctype="multipart/form-data" style="margin:0; width: 100%;">
           <label class="label-file importar" for="arquivo_importar">📥 Importar JSON</label>
           <input type="file" id="arquivo_importar" name="arquivo" accept=".json" onchange="this.form.submit()">
       </form>
   </div>
   <div class="botao-grupo">
       <form action="/mesclar" method="POST" enctype="multipart/form-data" style="margin:0; width: 100%;">
           <label class="label-file mesclar" for="arquivo_mesclar">🔀 Mesclar JSON</label>
           <input type="file" id="arquivo_mesclar" name="arquivo" accept=".json" onchange="this.form.submit()">
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

@app.route("/")
def index():
   dados = carregar_dados()
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
       HTML,
       abas=dados["abas"],
       treinos=treinos,
       mensagem=mensagem,
       tipo_mensagem=tipo_mensagem
   )

# Exportar JSON
@app.route("/exportar", methods=["GET"])
def exportar():
   try:
       dados = carregar_dados()
       json_str = json.dumps(dados, ensure_ascii=False, indent=4)
       buffer = BytesIO(json_str.encode('utf-8'))
       return send_file(
           buffer,
           mimetype='application/json',
           as_attachment=True,
           download_name='treinos.json'
       )
   except Exception as e:
       return redirect(f"/?mensagem=Erro ao exportar: {str(e)}&tipo=erro")

# Importar JSON (substituir)
@app.route("/importar", methods=["POST"])
def importar():
   try:
       if 'arquivo' not in request.files:
           return redirect("/?mensagem=Nenhum arquivo selecionado&tipo=erro")
       
       arquivo = request.files['arquivo']
       
       if arquivo.filename == '':
           return redirect("/?mensagem=Nenhum arquivo selecionado&tipo=erro")
       
       # Validar se é JSON
       try:
           conteudo = json.loads(arquivo.read().decode('utf-8'))
       except json.JSONDecodeError:
           return redirect("/?mensagem=Arquivo JSON inválido&tipo=erro")
       
       # Validar estrutura básica
       if 'abas' not in conteudo or 'treinos' not in conteudo:
           return redirect("/?mensagem=Estrutura de JSON inválida. Deve conter 'abas' e 'treinos'&tipo=erro")
       
       # Salvar dados
       salvar_dados(conteudo)
       return redirect("/?mensagem=Dados importados com sucesso! (Substituído)&tipo=sucesso")
       
   except Exception as e:
       return redirect(f"/?mensagem=Erro ao importar: {str(e)}&tipo=erro")

# Mesclar JSON
@app.route("/mesclar", methods=["POST"])
def mesclar():
   try:
       if 'arquivo' not in request.files:
           return redirect("/?mensagem=Nenhum arquivo selecionado&tipo=erro")
       
       arquivo = request.files['arquivo']
       
       if arquivo.filename == '':
           return redirect("/?mensagem=Nenhum arquivo selecionado&tipo=erro")
       
       # Validar se é JSON
       try:
           conteudo_novo = json.loads(arquivo.read().decode('utf-8'))
       except json.JSONDecodeError:
           return redirect("/?mensagem=Arquivo JSON inválido&tipo=erro")
       
       # Validar estrutura básica
       if 'abas' not in conteudo_novo or 'treinos' not in conteudo_novo:
           return redirect("/?mensagem=Estrutura de JSON inválida. Deve conter 'abas' e 'treinos'&tipo=erro")
       
       # Carregar dados atuais
       dados_atuais = carregar_dados()
       
       # Mesclar abas (sem duplicatas por ID)
       ids_abas_atuais = {aba['id'] for aba in dados_atuais['abas']}
       for aba_nova in conteudo_novo['abas']:
           if aba_nova['id'] not in ids_abas_atuais:
               dados_atuais['abas'].append(aba_nova)
       
       # Mesclar treinos (sem duplicatas por ID)
       ids_treinos_atuais = {treino['id'] for treino in dados_atuais['treinos']}
       for treino_novo in conteudo_novo['treinos']:
           if treino_novo['id'] not in ids_treinos_atuais:
               dados_atuais['treinos'].append(treino_novo)
       
       # Salvar dados mesclados
       salvar_dados(dados_atuais)
       return redirect("/?mensagem=Dados mesclados com sucesso!&tipo=sucesso")
       
   except Exception as e:
       return redirect(f"/?mensagem=Erro ao mesclar: {str(e)}&tipo=erro")

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
   port = os.environ.get('PORT', 5000)
   app.run(
       host="0.0.0.0",
       port=int(port),
       debug=False
   )
