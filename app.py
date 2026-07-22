import customtkinter as ctk
from tkcalendar import DateEntry
from datetime import timedelta
 
# ==========================================
# CONFIGURAÇÃO VISUAL
# ==========================================
 
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
 
 
# ==========================================
# FUNÇÕES
# ==========================================
 
def obter_sabado(data):
    wd = data.weekday()
 
    if wd == 5:  # sábado
        return data
 
    if wd == 6:  # domingo
        return data - timedelta(days=1)
 
    return data - timedelta(days=wd + 2)
 
 
def verificar():
 
    referencia = data_referencia.get_date()
    evento = data_evento.get_date()
 
    sab_ref = obter_sabado(referencia)
    sab_evento = obter_sabado(evento)
 
    diferenca_semanas = (sab_evento - sab_ref).days // 7
 
    inicio_periodo = sab_evento
    fim_periodo = sab_evento + timedelta(days=1)
 
    if diferenca_semanas % 2 == 0:
 
        resultado.configure(
            text=(
                "✅ VOCÊ ESTARÁ COM SUAS FILHAS\n\n"
                f"Período: {inicio_periodo.strftime('%d/%m/%Y')} "
                f"até {fim_periodo.strftime('%d/%m/%Y')}"
            ),
            fg_color="#2E7D32",
            text_color="white"
        )
 
    else:
 
        resultado.configure(
            text=(
                "❌ VOCÊ NÃO ESTARÁ COM SUAS FILHAS\n\n"
                f"Final de semana: {inicio_periodo.strftime('%d/%m/%Y')} "
                f"até {fim_periodo.strftime('%d/%m/%Y')}"
            ),
            fg_color="#C62828",
            text_color="white"
        )
 
 
def listar_periodos():
 
    referencia = data_referencia.get_date()
    sabado = obter_sabado(referencia)
 
    janela_lista = ctk.CTkToplevel(app)
    janela_lista.title("Próximos Finais de Semana")
    janela_lista.geometry("900x600")
 
    titulo = ctk.CTkLabel(
        janela_lista,
        text="PRÓXIMOS FINAIS DE SEMANA",
        font=("Segoe UI", 22, "bold")
    )
 
    titulo.pack(pady=15)
 
    texto = ctk.CTkTextbox(
        janela_lista,
        width=850,
        height=500,
        font=("Consolas", 13)
    )
 
    texto.pack(
        padx=20,
        pady=10,
        fill="both",
        expand=True
    )
 
    texto.insert(
        "end",
        "INÍCIO       FIM          STATUS\n"
    )
 
    texto.insert(
        "end",
        "-" * 80 + "\n"
    )
 
    for i in range(52):
 
        inicio = sabado + timedelta(days=i * 7)
        fim = inicio + timedelta(days=1)
 
        if i % 2 == 0:
            status = "✅ COM AS FILHAS"
        else:
            status = "❌ SEM AS FILHAS"
 
        linha = (
            f"{inicio.strftime('%d/%m/%Y')}   "
            f"{fim.strftime('%d/%m/%Y')}   "
            f"{status}\n"
        )
 
        texto.insert("end", linha)
 
    texto.configure(state="disabled")
 
 
# ==========================================
# JANELA PRINCIPAL
# ==========================================
 
app = ctk.CTk()
 
app.title("Controle de Guarda das Filhas")
app.geometry("750x550")
 
# Título
 
titulo = ctk.CTkLabel(
    app,
    text="CONTROLE DE GUARDA DAS FILHAS",
    font=("Segoe UI", 26, "bold")
)
 
titulo.pack(pady=20)
 
# Frame principal
 
frame = ctk.CTkFrame(app)
frame.pack(
    padx=30,
    pady=20,
    fill="both",
    expand=True
)
 
# Data referência
 
label_ref = ctk.CTkLabel(
    frame,
    text="Data em que você estava com suas filhas",
    font=("Segoe UI", 14)
)
 
label_ref.pack(pady=(25, 5))
 
data_referencia = DateEntry(
    frame,
    locale="pt_BR",
    date_pattern="dd/mm/yyyy",
    width=20,
    background="#1F6AA5",
    foreground="white",
    borderwidth=2
)
 
data_referencia.pack()
 
# Data evento
 
label_evento = ctk.CTkLabel(
    frame,
    text="Data do evento",
    font=("Segoe UI", 14)
)
 
label_evento.pack(pady=(20, 5))
 
data_evento = DateEntry(
    frame,
    locale="pt_BR",
    date_pattern="dd/mm/yyyy",
    width=20,
    background="#1F6AA5",
    foreground="white",
    borderwidth=2
)
 
data_evento.pack()
 
# Botão verificar
 
botao_verificar = ctk.CTkButton(
    frame,
    text="Verificar Evento",
    command=verificar,
    width=250,
    height=40,
    font=("Segoe UI", 14, "bold")
)
 
botao_verificar.pack(pady=20)
 
# Botão listar
 
botao_lista = ctk.CTkButton(
    frame,
    text="Próximos Finais de Semana",
    command=listar_periodos,
    width=250,
    height=40,
    font=("Segoe UI", 14, "bold")
)
 
botao_lista.pack()
 
# Resultado
 
resultado = ctk.CTkLabel(
    frame,
    text="",
    height=90,
    corner_radius=12,
    font=("Segoe UI", 15, "bold")
)
 
resultado.pack(
    pady=30,
    padx=20,
    fill="x"
)
 
# Rodar aplicação
 
app.mainloop()
