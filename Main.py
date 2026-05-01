import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="CheckPoint Ganhos 💰", layout="wide")

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), 
                    url("https://images.unsplash.com/photo-1554224155-6726b3ff858f?q=80&w=2011&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
    }
    [data-testid="stForm"], div[data-testid="stVerticalBlock"] > div {
        background-color: rgba(255, 255, 255, 0.07) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px !important;
        padding: 20px;
    }
    .card-meta { padding: 30px; border-radius: 20px; text-align: center; margin: 20px 0; border: 3px solid; }
    .meta-sucesso { background-color: rgba(0, 255, 127, 0.2); border-color: #00FF7F; color: #00FF7F; }
    .meta-falta { background-color: rgba(255, 75, 75, 0.2); border-color: #FF4B4B; color: #FF4B4B; }
    h1, h2, h3, h4, label, p, span { color: white !important; }
</style>
""", unsafe_allow_html=True)

def conectar():
    conn = sqlite3.connect("ganhos_shift.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS ganhos (id INTEGER PRIMARY KEY, usuario TEXT, data TEXT, ganho REAL, gasto REAL, km REAL, h_ini TEXT, h_fim TEXT)")
    # Tabela para as Listas Calculadoras
    cursor.execute("CREATE TABLE IF NOT EXISTS calc_listas (id INTEGER PRIMARY KEY, usuario TEXT, nome_lista TEXT, valor REAL, descricao TEXT)")
    conn.commit()
    return conn, cursor

conn, cursor = conectar()

if "autenticado" not in st.session_state: st.session_state.autenticado = False

# --- TELA DE ACESSO ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>💰 CheckPoint Ganhos</h1>", unsafe_allow_html=True)
    aba_login, aba_cad = st.tabs(["🔑 ACESSAR", "📝 CRIAR CONTA"])
    with aba_login:
        u = st.text_input("Usuário").lower().strip()
        s = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            if cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s)).fetchone():
                st.session_state.autenticado, st.session_state.user = True, u
                st.rerun()
    with aba_cad:
        nu = st.text_input("Novo Usuário").lower().strip()
        ns = st.text_input("Nova Senha", type="password")
        if st.button("CADASTRAR"):
            try:
                cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?,?)", (nu, ns))
                conn.commit(); st.success("Conta criada!")
            except: st.error("Erro ao criar conta.")
    st.stop()

user = st.session_state.user

# --- DASHBOARD ---
st.title(f"🚀 PAINEL: {user.upper()}")
tab_ganhos, tab_calc = st.tabs(["💰 RELATÓRIO FINAL", "🧮 CALCULADORA DE LISTAS"])

# --- ABA 1: RELATÓRIO FINAL (Onde você joga o total do dia) ---
with tab_ganhos:
    with st.form("job_final"):
        st.subheader("🏁 Fechamento do Dia")
        c1, c2, c3 = st.columns(3)
        v_bruto = c1.number_input("Ganho Total Bruto (R$)", min_value=0.0)
        v_gasto = c2.number_input("Gasto Total (R$)", min_value=0.0)
        v_km = c3.number_input("KM Total", step=1.0)
        if st.form_submit_button("SALVAR NO HISTÓRICO"):
            cursor.execute("INSERT INTO ganhos (usuario, data, ganho, gasto, km, h_ini, h_fim) VALUES (?,?,?,?,?,?,?)", 
                           (user, str(date.today()), v_bruto, v_gasto, v_km, "00:00", "00:00"))
            conn.commit(); st.rerun()
    
    # Histórico simplificado
    df_g = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{user}'", conn)
    if not df_g.empty:
        for _, r in df_g.sort_values(by='id', ascending=False).iterrows():
            st.write(f"📅 {r['data']} | Lucro: **R$ {r['ganho']-r['gasto']:.2f}**")

# --- ABA 2: CALCULADORA DE LISTAS (O "Somador" que você pediu) ---
with tab_calc:
    st.subheader("🧮 Minhas Listas de Soma")
    st.info("Crie listas para somar ganhos picados ou gastos do dia a dia.")

    # Criar nova lista
    nova_lista = st.text_input("Nome da Nova Lista (ex: Ganhos Manhã, Gastos Comida):")
    if st.button("➕ Criar Nova Lista"):
        if nova_lista:
            # Insere um valor zero apenas para "abrir" a lista
            cursor.execute("INSERT INTO calc_listas (usuario, nome_lista, valor, descricao) VALUES (?,?,?,?)", (user, nova_lista, 0.0, "Início"))
            conn.commit(); st.rerun()

    st.markdown("---")

    # Mostrar listas existentes
    listas_nomes = pd.read_sql_query(f"SELECT DISTINCT nome_lista FROM calc_listas WHERE usuario='{user}'", conn)
    
    for nome in listas_nomes['nome_lista']:
        with st.expander(f"📋 LISTA: {nome.upper()}", expanded=True):
            # Buscar itens dessa lista
            itens = pd.read_sql_query(f"SELECT * FROM calc_listas WHERE usuario='{user}' AND nome_lista='{nome}'", conn)
            total_lista = itens['valor'].sum()
            
            st.markdown(f"### TOTAL: **R$ {total_lista:.2f}**")
            
            # Adicionar valor à lista
            with st.form(f"add_{nome}"):
                c1, c2 = st.columns([0.3, 0.7])
                val_add = c1.number_input("Valor R$", min_value=0.0, key=f"val_{nome}")
                desc_add = c2.text_input("O que é?", placeholder="ex: Entrega X, Almoço...", key=f"desc_{nome}")
                if st.form_submit_button("Somar na Lista"):
                    cursor.execute("INSERT INTO calc_listas (usuario, nome_lista, valor, descricao) VALUES (?,?,?,?)", (user, nome, val_add, desc_add))
                    conn.commit(); st.rerun()
            
            # Mostrar histórico da lista
            for _, item in itens.iterrows():
                if item['valor'] > 0:
                    col_i1, col_i2 = st.columns([0.8, 0.2])
                    col_i1.write(f"R$ {item['valor']:.2f} - {item['descricao']}")
                    if col_i2.button("❌", key=f"del_item_{item['id']}"):
                        cursor.execute("DELETE FROM calc_listas WHERE id=?", (item['id'],))
                        conn.commit(); st.rerun()
            
            if st.button(f"🗑️ APAGAR LISTA INTEIRA ({nome})", key=f"del_lista_{nome}"):
                cursor.execute("DELETE FROM calc_listas WHERE usuario=? AND nome_lista=?", (user, nome))
                conn.commit(); st.rerun()

# --- BARRA LATERAL ---
st.sidebar.markdown("---")
if st.sidebar.button("🚪 SAIR"):
    st.session_state.autenticado = False
    st.rerun()
