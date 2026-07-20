from flask import Flask, render_template_string, request, redirect
import json
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Conectar ao PostgreSQL no Render
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """Criar tabelas se não existirem"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS abas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS treinos (
            id SERIAL PRIMARY KEY,
            aba_id INTEGER NOT NULL REFERENCES abas(id) ON DELETE CASCADE,
            nome VARCHAR(255) NOT NULL,
            imagem TEXT,
            series VARCHAR(255),
            repeticoes VARCHAR(255),
            observacoes TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id SERIAL PRIMARY KEY,
            treino_id INTEGER NOT NULL REFERENCES treinos(id) ON DELETE CASCADE,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            peso VARCHAR(255),
            reps VARCHAR(255)
        )
    """)
    
    # Inserir aba padrão se não existir
    cur.execute("SELECT COUNT(*) FROM abas")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO abas (nome) VALUES (%s)", ("Treino A",))
    
    conn.commit()
    cur.close()
    conn.close()

# Inicializar banco
init_db()

# Carregar dados para exibição
def carregar_dados():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT * FROM abas ORDER BY id")
    abas = cur.fetchall()
    
    cur.execute("SELECT * FROM treinos ORDER BY id")
    treinos = cur.fetchall()
    
    # Buscar histórico para cada treino
    for treino in treinos:
        cur.execute("""
            SELECT data, peso, reps FROM historico 
            WHERE treino_id = %s ORDER BY data DESC
        """, (treino['id'],))
        treino['historico'] = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return {
        "abas": abas,
        "treinos": treinos
    }

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
   {% for item in treino.historico %}
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
           if treino['aba_id'] == int(aba_id)
       ]
   return render_template_string(
       HTML,
       abas=dados["abas"],
       treinos=treinos
   )

@app.route("/criar_aba", methods=["POST"])
def criar_aba():
   nome = request.form["nome"]
   conn = get_db_connection()
   cur = conn.cursor()
   cur.execute("INSERT INTO abas (nome) VALUES (%s)", (nome,))
   conn.commit()
   cur.close()
   conn.close()
   return redirect("/")

@app.route("/editar_aba/<int:id>", methods=["GET", "POST"])
def editar_aba(id):
   conn = get_db_connection()
   cur = conn.cursor(cursor_factory=RealDictCursor)
   
   if request.method == "POST":
       nome = request.form["nome"]
       cur.execute("UPDATE abas SET nome = %s WHERE id = %s", (nome, id))
       conn.commit()
       cur.close()
       conn.close()
       return redirect("/")
   
   cur.execute("SELECT * FROM abas WHERE id = %s", (id,))
   aba = cur.fetchone()
   cur.close()
   conn.close()
   
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
   conn = get_db_connection()
   cur = conn.cursor()
   cur.execute("DELETE FROM abas WHERE id = %s", (id,))
   conn.commit()
   cur.close()
   conn.close()
   return redirect("/")

@app.route("/adicionar", methods=["POST"])
def adicionar():
   aba_id = int(request.form["aba_id"])
   nome = request.form["nome"]
   imagem = request.form["imagem"]
   series = request.form["series"]
   repeticoes = request.form["repeticoes"]
   observacoes = request.form["observacoes"]
   
   conn = get_db_connection()
   cur = conn.cursor()
   cur.execute("""
       INSERT INTO treinos (aba_id, nome, imagem, series, repeticoes, observacoes)
       VALUES (%s, %s, %s, %s, %s, %s)
   """, (aba_id, nome, imagem, series, repeticoes, observacoes))
   conn.commit()
   cur.close()
   conn.close()
   
   return redirect(f"/?aba={aba_id}")

@app.route("/registrar/<int:id>", methods=["POST"])
def registrar(id):
   peso = request.form["peso"]
   reps = request.form["reps"]
   
   conn = get_db_connection()
   cur = conn.cursor()
   cur.execute("""
       INSERT INTO historico (treino_id, peso, reps)
       VALUES (%s, %s, %s)
   """, (id, peso, reps))
   conn.commit()
   cur.close()
   conn.close()
   
   return redirect("/")

@app.route("/excluir/<int:id>")
def excluir(id):
   conn = get_db_connection()
   cur = conn.cursor()
   cur.execute("DELETE FROM treinos WHERE id = %s", (id,))
   conn.commit()
   cur.close()
   conn.close()
   return redirect("/")

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
   conn = get_db_connection()
   cur = conn.cursor(cursor_factory=RealDictCursor)
   
   if request.method == "POST":
       nome = request.form["nome"]
       imagem = request.form["imagem"]
       series = request.form["series"]
       repeticoes = request.form["repeticoes"]
       observacoes = request.form["observacoes"]
       
       cur.execute("""
           UPDATE treinos 
           SET nome = %s, imagem = %s, series = %s, repeticoes = %s, observacoes = %s
           WHERE id = %s
       """, (nome, imagem, series, repeticoes, observacoes, id))
       conn.commit()
       cur.close()
       conn.close()
       return redirect("/")
   
   cur.execute("SELECT * FROM treinos WHERE id = %s", (id,))
   treino = cur.fetchone()
   cur.close()
   conn.close()
   
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
           value="{treino['imagem'] or ''}"
           style="width:100%;padding:12px;margin-top:10px;border:none;border-radius:10px;"
>
<input
           type="text"
           name="series"
           value="{treino['series'] or ''}"
           style="width:100%;padding:12px;margin-top:10px;border:none;border-radius:10px;"
>
<input
           type="text"
           name="repeticoes"
           value="{treino['repeticoes'] or ''}"
           style="width:100%;padding:12px;margin-top:10px;border:none;border-radius:10px;"
>
<textarea
           name="observacoes"
           style="width:100%;height:100px;padding:12px;margin-top:10px;border:none;border-radius:10px;"
>{treino['observacoes'] or ''}</textarea>
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
