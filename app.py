from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os


def obter_sabado(data):
    wd = data.weekday()

    if wd == 5:  # sábado
        return data

    if wd == 6:  # domingo
        return data - timedelta(days=1)

    return data - timedelta(days=wd + 2)


def format_date(d):
    return d.strftime('%d/%m/%Y')


app = Flask(__name__)


@app.route('/')
def index():
    today = datetime.today().date()
    return render_template('index.html', today=today.strftime('%Y-%m-%d'))


@app.route('/verificar', methods=['POST'])
def verificar():
    ref = request.form.get('data_referencia')
    evento = request.form.get('data_evento')

    try:
        ref_date = datetime.strptime(ref, '%Y-%m-%d').date()
        ev_date = datetime.strptime(evento, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'error': 'Formato de data inválido'}), 400

    sab_ref = obter_sabado(ref_date)
    sab_evento = obter_sabado(ev_date)
    diferenca_semanas = (sab_evento - sab_ref).days // 7

    inicio = sab_evento
    fim = sab_evento + timedelta(days=1)

    if diferenca_semanas % 2 == 0:
        text = (
            "✅ VOCÊ ESTARÁ COM SUAS FILHAS\n"
            f"Período: {format_date(inicio)} até {format_date(fim)}"
        )
        color = 'success'
    else:
        text = (
            "❌ VOCÊ NÃO ESTARÁ COM SUAS FILHAS\n"
            f"Final de semana: {format_date(inicio)} até {format_date(fim)}"
        )
        color = 'danger'

    return jsonify({
        'text': text,
        'inicio': format_date(inicio),
        'fim': format_date(fim),
        'color': color,
    })


@app.route('/listar')
def listar():
    ref = request.args.get('data_referencia')
    if not ref:
        ref_date = datetime.today().date()
    else:
        try:
            ref_date = datetime.strptime(ref, '%Y-%m-%d').date()
        except Exception:
            ref_date = datetime.today().date()

    sabado = obter_sabado(ref_date)
    items = []
    for i in range(52):
        inicio = sabado + timedelta(days=i * 7)
        fim = inicio + timedelta(days=1)
        status = '✅ COM AS FILHAS' if i % 2 == 0 else '❌ SEM AS FILHAS'
        items.append({'inicio': format_date(inicio), 'fim': format_date(fim), 'status': status})

    return render_template('list.html', items=items)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
