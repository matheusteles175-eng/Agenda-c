import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="CheckPoint Pro", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    /* Card de Total Destacado */
    .total-card {
        background: linear-gradient(135.deg, #2E7D32, #1B5E20);
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 10px;
        border: 1px solid #4CAF50;
    }
    /* Deixar os inputs mais compactos */
    .stNumberInput, .stTextInput { margin-bottom: -15px; }
    [data-testid="stForm"] { padding: 10px !important; border-radius: 15px !important; }
    h1, h2, h3, p { color: white !important; margin: 0px !important; }
    .item-lista {
        background: rgba(255, 255, 255, 0.05);
        padding: 8px;
        border-radius: 8px;
        margin-bottom: 5px;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

def conectar():
    conn = sqlite3.connect("ganhos_shift.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS ganhos (id INTEGER PRIMARY KEY, usuario TEXT, data TEXT, ganho REAL, gasto REAL, km REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS calc_listas (id INTEGER PRIMARY KEY, usuario TEXT, nome_lista TEXT, valor REAL, descricao TEXT)")
    conn.commit()
    return conn, cursor

conn, cursor = conectar()

if "autenticado" not in st.session_state: st.session_state.autenticado = False

# --- ACESSO ---
if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center;'>💰 CheckPoint Ganhos</h2>", unsafe_allow_html=True)
    u = st.text_input("Usuário").lower().strip()
    s = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s)).fetchone():
            st.session_state.autenticado, st.session_state.user = True, u
            st.rerun()
    st.stop()

user = st.session_state.user

# --- INTERFACE PRINCIPAL ---
st.write(f"Usuário: **{user.upper()}**")
tab_calc, tab_hist = st.tabs(["🧮 CALCULADORA", "📊 HISTÓRICO"])

with tab_calc:
    # 1. Seleção da Lista (Bem compacta)
    listas_nomes = pd.read_sql_query(f"SELECT DISTINCT nome_lista FROM calc_listas WHERE usuario='{user}'", conn)
    
    col_sel, col_add = st.columns([0.6, 0.4])
    lista_selecionada = col_sel.selectbox("Lista Ativa:", listas_nomes['nome_lista'] if not listas_nomes.empty else ["Crie uma lista"])
    
    if col_add.button("➕ Nova Lista"):
        st.session_state.criando_lista = True

    if st.session_state.get("criando_lista"):
        with st.form("nova_l"):
            n_l = st.text_input("Nome (ex: Ganhos)")
            if st.form_submit_button("Criar"):
                cursor.execute("INSERT INTO calc_listas (usuario, nome_lista, valor, descricao) VALUES (?,?,?,?)", (user, n_l, 0.0, "Início"))
                conn.commit()
                st.session_state.criando_lista = False
                st.rerun()

    if not listas_nomes.empty:
        # 2. TOTAL FIXO NO TOPO (A pessoa vê o resultado na hora)
        itens = pd.read_sql_query(f"SELECT * FROM calc_listas WHERE usuario='{user}' AND nome_lista='{lista_selecionada}'", conn)
        total_atual = itens['valor'].sum()
        
        st.markdown(f"""
            <div class="total-card">
                <p style="font-size: 16px; opacity: 0.8;">Total da Lista</p>
                <h1 style="font-size: 45px;">R$ {total_atual:.2f}</h1>
            </div>
        """, unsafe_allow_html=True)

        # 3. CAMPO DE ENTRADA (Logo abaixo do total)
        with st.form(f"add_val", clear_on_submit=True):
            c1, c2 = st.columns([0.4, 0.6])
            v_input = c1.number_input("R$", min_value=0.0, step=1.0, format="%.2f")
            d_input = c2.text_input("Descrição (opcional)")
            if st.form_submit_button("➕ SOMAR AGORA", use_container_width=True):
                if v_input > 0:
                    cursor.execute("INSERT INTO calc_listas (usuario, nome_lista, valor, descricao) VALUES (?,?,?,?)", 
                                   (user, lista_selecionada, v_input, d_input))
                    conn.commit()
                    st.rerun()

        # 4. BOTÕES DE AÇÃO RÁPIDA
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("🧹 Limpar Valores"):
            cursor.execute("DELETE FROM calc_listas WHERE usuario=? AND nome_lista=?", (user, lista_selecionada))
            cursor.execute("INSERT INTO calc_listas (usuario, nome_lista, valor, descricao) VALUES (?,?,?,?)", (user, lista_selecionada, 0.0, "Reset"))
            conn.commit()
            st.rerun()
        
        if col_btn2.button("💾 Salvar no Dia"):
             # Simplesmente envia o total para o histórico do dia
             cursor.execute("INSERT INTO ganhos (usuario, data, ganho, gasto, km) VALUES (?,?,?,?,?)", 
                            (user, str(date.today()), total_atual, 0.0, 0.0))
             conn.commit()
             st.success("Salvo no Histórico!")

        # 5. HISTÓRICO RECENTE (Fica lá embaixo, só para conferência)
        with st.expander("Ver itens somados"):
            for _, item in itens.sort_values(by='id', ascending=False).iterrows():
                if item['valor'] > 0:
                    st.markdown(f"""<div class="item-lista">R$ {item['valor']:.2f} <small>({item['descricao']})</small></div>""", unsafe_allow_html=True)

with tab_hist:
    df_h = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{user}'", conn)
    if not df_h.empty:
        st.dataframe(df_h[['data', 'ganho']].sort_values(by='data', ascending=False), hide_index=True)
    else:
        st.write("Nenhum dia salvo ainda.")

# Sair
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()
