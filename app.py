from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import json
import os
import calendar
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import openpyxl
from openpyxl.styles import PatternFill, Alignment, Font

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

ARQUIVO_HISTORICO = "historico_consultas.json"
ARQUIVO_CONFIGURACAO = "configuracao.json"

CONFIG_PADRAO = {
    "data_referencia": None,
    "tema": "light",
}

# ==========================================
# GERENCIADOR DE DADOS
# ==========================================

class GerenciadorDados:
    def __init__(self):
        self.config = self.carregar_config()
        self.historico = self.carregar_historico()
    
    def carregar_config(self):
        if os.path.exists(ARQUIVO_CONFIGURACAO):
            try:
                with open(ARQUIVO_CONFIGURACAO, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return CONFIG_PADRAO.copy()
        return CONFIG_PADRAO.copy()
    
    def salvar_config(self):
        with open(ARQUIVO_CONFIGURACAO, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2, default=str)
    
    def carregar_historico(self):
        if os.path.exists(ARQUIVO_HISTORICO):
            try:
                with open(ARQUIVO_HISTORICO, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def salvar_historico(self):
        with open(ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f:
            json.dump(self.historico, f, ensure_ascii=False, indent=2, default=str)
    
    def adicionar_consulta(self, data):
        self.historico.append({
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        self.salvar_historico()

dados = GerenciadorDados()

# ==========================================
# FUNÇÕES DE CÁLCULO
# ==========================================

def obter_sabado(data):
    """Obtém o sábado da semana atual"""
    if isinstance(data, str):
        data = datetime.strptime(data, '%Y-%m-%d').date()
    
    wd = data.weekday()
    
    if wd == 5:  # sábado
        return data
    
    if wd == 6:  # domingo
        return data - timedelta(days=1)
    
    return data - timedelta(days=wd + 2)


def calcular_periodos(data_inicio, num_semanas=52):
    """Calcula períodos baseado na data de início"""
    if isinstance(data_inicio, str):
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    
    sabado = obter_sabado(data_inicio)
    periodos = []
    
    for i in range(num_semanas):
        inicio = sabado + timedelta(days=i * 14)
        fim = inicio + timedelta(days=1)
        tem_filhas = (i % 2 == 0)
        
        periodos.append({
            'inicio': inicio.strftime('%Y-%m-%d'),
            'fim': fim.strftime('%Y-%m-%d'),
            'tem_filhas': tem_filhas,
            'semana': i
        })
    
    return periodos


def obter_proximos_periodos(data_referencia, num_periodos=5):
    """Obtém os próximos períodos com as filhas"""
    if isinstance(data_referencia, str):
        data_referencia = datetime.strptime(data_referencia, '%Y-%m-%d').date()
    
    periodos = calcular_periodos(data_referencia, num_semanas=52)
    proximos = []
    
    for p in periodos:
        inicio = datetime.strptime(p['inicio'], '%Y-%m-%d').date()
        if p['tem_filhas'] and inicio >= data_referencia:
            proximos.append(p)
    
    return proximos[:num_periodos]


def calcular_dias_faltantes(data_str):
    """Calcula quantos dias faltam até a data"""
    data = datetime.strptime(data_str, '%Y-%m-%d').date()
    hoje = datetime.now().date()
    if data < hoje:
        return 0
    diferenca = (data - hoje).days
    return diferenca


def verificar_evento(data_evento_str, data_referencia_str):
    """Verifica se haverá guarda no dia do evento"""
    data_evento = datetime.strptime(data_evento_str, '%Y-%m-%d').date()
    data_referencia = datetime.strptime(data_referencia_str, '%Y-%m-%d').date()
    
    sab_ref = obter_sabado(data_referencia)
    sab_evento = obter_sabado(data_evento)
    
    diferenca_semanas = (sab_evento - sab_ref).days // 7
    
    tem_filhas = (diferenca_semanas % 2 == 0)
    
    return {
        'tem_filhas': tem_filhas,
        'inicio': sab_evento.strftime('%Y-%m-%d'),
        'fim': (sab_evento + timedelta(days=1)).strftime('%Y-%m-%d')
    }


def contar_periodos_ano(data_referencia, ano, tem_filhas=True):
    """Conta quantos períodos com/sem filhas em um determinado ano"""
    if isinstance(data_referencia, str):
        data_referencia = datetime.strptime(data_referencia, '%Y-%m-%d').date()
    
    periodos = calcular_periodos(data_referencia, num_semanas=260)
    
    contagem = 0
    for p in periodos:
        inicio = datetime.strptime(p['inicio'], '%Y-%m-%d').date()
        if inicio.year == ano and p['tem_filhas'] == tem_filhas:
            contagem += 1
    
    return contagem


# ==========================================
# ROTAS
# ==========================================

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')


@app.route('/api/dashboard', methods=['POST'])
def dashboard():
    """Retorna dados do dashboard"""
    try:
        data = request.json
        data_referencia = data.get('data_referencia')
        
        dados.adicionar_consulta(data_referencia)
        
        proximos = obter_proximos_periodos(data_referencia, 1)
        proximos_5 = obter_proximos_periodos(data_referencia, 5)
        
        resultado = {
            'sucesso': True,
            'data': data_referencia
        }
        
        if proximos:
            proximo = proximos[0]
            dias_faltantes = calcular_dias_faltantes(proximo['inicio'])
            resultado['proximo'] = {
                'inicio': proximo['inicio'],
                'fim': proximo['fim'],
                'dias_faltantes': dias_faltantes
            }
        
        ano_atual = datetime.now().year
        resultado['total_com'] = contar_periodos_ano(data_referencia, ano_atual, tem_filhas=True)
        resultado['total_sem'] = contar_periodos_ano(data_referencia, ano_atual, tem_filhas=False)
        resultado['ano'] = ano_atual
        
        resultado['proximos_5'] = []
        for p in proximos_5:
            dias_faltam = calcular_dias_faltantes(p['inicio'])
            resultado['proximos_5'].append({
                'inicio': p['inicio'],
                'fim': p['fim'],
                'dias_faltantes': dias_faltam
            })
        
        return jsonify(resultado)
    
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 400


@app.route('/api/periodos', methods=['POST'])
def get_periodos():
    """Retorna períodos"""
    try:
        data = request.json
        data_referencia = data.get('data_referencia')
        num_semanas = data.get('num_semanas', 52)
        
        periodos = calcular_periodos(data_referencia, num_semanas)
        
        return jsonify({
            'sucesso': True,
            'periodos': periodos
        })
    
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 400


@app.route('/api/calendario', methods=['POST'])
def get_calendario():
    """Retorna dados do calendário"""
    try:
        data = request.json
        data_referencia = data.get('data_referencia')
        mes = data.get('mes')
        ano = data.get('ano')
        
        periodos = calcular_periodos(data_referencia, num_semanas=260)
        
        # Criar mapa de dias com filhas
        dias_com_filhas = set()
        for p in periodos:
            inicio = datetime.strptime(p['inicio'], '%Y-%m-%d').date()
            fim = datetime.strptime(p['fim'], '%Y-%m-%d').date()
            
            if p['tem_filhas'] and inicio.year == ano and inicio.month == mes:
                current = inicio
                while current <= fim and current.year == ano and current.month == mes:
                    dias_com_filhas.add(current.day)
                    current += timedelta(days=1)
        
        return jsonify({
            'sucesso': True,
            'dias_com_filhas': list(dias_com_filhas),
            'mes': mes,
            'ano': ano
        })
    
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 400


@app.route('/api/pesquisar', methods=['POST'])
def pesquisar_data():
    """Pesquisa uma data específica"""
    try:
        data = request.json
        data_referencia = data.get('data_referencia')
        data_evento = data.get('data_evento')
        
        resultado = verificar_evento(data_evento, data_referencia)
        dias_faltantes = calcular_dias_faltantes(resultado['inicio'])
        
        return jsonify({
            'sucesso': True,
            'tem_filhas': resultado['tem_filhas'],
            'inicio': resultado['inicio'],
            'fim': resultado['fim'],
            'dias_faltantes': dias_faltantes
        })
    
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 400


@app.route('/api/historico')
def get_historico():
    """Retorna histórico de consultas"""
    return jsonify({
        'sucesso': True,
        'historico': dados.historico[-20:]
    })


@app.route('/api/mensagem-whatsapp', methods=['POST'])
def gerar_mensagem_whatsapp():
    """Gera mensagem para WhatsApp"""
    try:
        data = request.json
        data_referencia = data.get('data_referencia')
        
        periodos = obter_proximos_periodos(data_referencia, 10)
        
        mensagem = "Conforme meu calendário de guarda, estarei com minhas filhas nos dias:\n\n"
        
        for periodo in periodos:
            inicio = datetime.strptime(periodo['inicio'], '%Y-%m-%d').date()
            fim = datetime.strptime(periodo['fim'], '%Y-%m-%d').date()
            mensagem += f"📅 {inicio.strftime('%d/%m/%Y')} até {fim.strftime('%d/%m/%Y')}\n"
        
        return jsonify({
            'sucesso': True,
            'mensagem': mensagem
        })
    
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 400


@app.route('/api/exportar-pdf', methods=['POST'])
def exportar_pdf():
    """Exporta em PDF"""
    try:
        data = request.json
        data_referencia = data.get('data_referencia')
        
        periodos = calcular_periodos(data_referencia, num_semanas=52)
        
        # Criar PDF em memória
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        style_titulo = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#2E7D32',
            spaceAfter=30,
            alignment=1
        )
        
        elements.append(Paragraph("CALENDÁRIO DE GUARDA DAS FILHAS", style_titulo))
        elements.append(Paragraph(f"Ano: {datetime.now().year}", styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabela
        data_tabela = [["Período", "Início", "Fim", "Status"]]
        
        for i, periodo in enumerate(periodos, 1):
            status = "✅ COM AS FILHAS" if periodo['tem_filhas'] else "❌ SEM AS FILHAS"
            inicio = datetime.strptime(periodo['inicio'], '%Y-%m-%d').date()
            fim = datetime.strptime(periodo['fim'], '%Y-%m-%d').date()
            
            data_tabela.append([
                str(i),
                inicio.strftime('%d/%m/%Y'),
                fim.strftime('%d/%m/%Y'),
                status
            ])
        
        table = Table(data_tabela)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#2E7D32'),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, 'black'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), ['white', '#f0f0f0'])
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'calendario_guarda_{datetime.now().year}.pdf'
        )
    
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 400


@app.route('/api/exportar-excel', methods=['POST'])
def exportar_excel():
    """Exporta em Excel"""
    try:
        data = request.json
        data_referencia = data.get('data_referencia')
        
        periodos = calcular_periodos(data_referencia, num_semanas=52)
        
        # Criar Excel em memória
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Períodos"
        
        headers = ["Período", "Início", "Fim", "Status"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        for row, periodo in enumerate(periodos, 2):
            status = "✅ COM AS FILHAS" if periodo['tem_filhas'] else "❌ SEM AS FILHAS"
            inicio = datetime.strptime(periodo['inicio'], '%Y-%m-%d').date()
            fim = datetime.strptime(periodo['fim'], '%Y-%m-%d').date()
            
            ws.cell(row=row, column=1).value = row - 1
            ws.cell(row=row, column=2).value = inicio.strftime('%d/%m/%Y')
            ws.cell(row=row, column=3).value = fim.strftime('%d/%m/%Y')
            ws.cell(row=row, column=4).value = status
            
            cor = "C8E6C9" if periodo['tem_filhas'] else "FFCDD2"
            for col in range(1, 5):
                ws.cell(row=row, column=col).fill = PatternFill(
                    start_color=cor,
                    end_color=cor,
                    fill_type="solid"
                )
            
            for col in range(1, 5):
                ws.cell(row=row, column=col).alignment = Alignment(horizontal="center")
        
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 20
        
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'calendario_guarda_{datetime.now().year}.xlsx'
        )
    
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
