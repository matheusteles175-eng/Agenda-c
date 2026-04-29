import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. CONFIGURAÇÃO E ESTILO (VISUAL PROFISSIONAL) ---
st.set_page_config(page_title="CheckPoint Shift 🏁", layout="wide")

# CSS para remover o pano branco, aumentar ícones e destacar botões
st.markdown("""
<style>
    /* Fundo Principal com sobreposição escura para leitura */
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), 
                    url("https://images.unsplash.com/photo-1614850523296-d8c1af93d400?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
    }

    /* Estilo das Abas (Ícones Maiores) */
    .stTabs [data-baseweb="tab"] {
        color: white !important;
        font-size: 22px !important;
        font-weight: bold;
        padding: 10px 20px;
    }

    /* Blocos de conteúdo (Efeito Vidro) */
    [data-testid="stForm"], .st-expander, .stMetric, div[data-testid="stVerticalBlock"] > div {
        background-color: rgba(255, 255, 255, 0.07) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px !important;
        padding: 20px;
        margin-bottom: 10px;
    }

    /* Botões Padrão (Maiores e Visíveis) */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
        font-size: 18px !important;
        height: 3.2em;
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 2px solid rgba(255, 255, 255, 0.4) !important;
        transition: 0.3s;
    }

    .stButton>button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #ffffff !important;
    }

    /* Estilo para as Lixeiras e Botões de Perigo (Vermelho) */
    div.stButton > button[key^="del_"], div.stButton > button:contains("ZERAR") {
        border: 2px solid #ff4b4b !important;
        color: #ff4b4b !important;
        background-color: rgba(255, 75, 75, 0.1) !important;
    }

    div.stButton > button[key^="del_"]:hover {
        background-color: #ff4b4b !important;
        color: white !important;
    }

    /* Textos e Títulos */
    h1, h2, h3, h4, label, p, span { color: #ffffff !important; text-shadow: 2px 2px 4px #000; }
    [data-testid="stMetricValue"] { font-size: 35px !important; color: #00FFCC !important; }
    
    /* Inputs (Onde digita) */
    input {
        background-color: rgba(0, 0, 0, 0.5) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

def conectar():
    conn = sqlite3.connect("checkpoint_shift_mateus.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS veiculo (usuario TEXT PRIMARY KEY, km_ini REAL, km_alvo REAL, custo REAL, fipe REAL, guardado_ipva REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY, usuario TEXT, item TEXT, valor REAL, data TEXT, guardado REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS ganhos (id INTEGER PRIMARY KEY, usuario TEXT, data TEXT, ganho REAL, gasto REAL, km REAL, h_ini TEXT, h_fim TEXT)")
    conn.commit()
    return conn, cursor

conn, cursor = conectar()

# --- 2. LOGIN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>🏁 CheckPoint Shift</h1>", unsafe_allow_html=True)
    aba_login, aba_cad = st.tabs(["🔑 ACESSAR", "📝 CRIAR CONTA"])
    with aba_login:
        u = st.text_input("Usuário").lower().strip()
        s = st.text_input("Senha", type="password")
        if st.button("ENTRAR NO PAINEL"):
            if cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s)).fetchone():
                st.session_state.autenticado, st.session_state.user = True, u
                st.rerun()
            else: st.error("Usuário ou senha incorretos.")
    with aba_cad:
        nu = st.text_input("Novo Usuário").lower().strip()
        ns = st.text_input("Sua Senha", type="password")
        if st.button("CADASTRAR E FINALIZAR"):
            try:
                cursor.execute("INSERT INTO usuarios VALUES (?,?)", (nu, ns))
                conn.commit(); st.success("✅ Conta criada! Volte na aba Acessar.")
            except: st.error("❌ Nome de usuário já existe.")
    st.stop()

user = st.session_state.user
hoje = date.today()

# --- 3. DADOS DO VEÍCULO ---
v_data = cursor.execute("SELECT * FROM veiculo WHERE usuario=?", (user,)).fetchone()
if v_data is None:
    st.header(f"Olá, {user.upper()}! 🚀")
    with st.form("cfg_carro"):
        f1 = st.number_input("Valor FIPE do Carro", value=45000.0)
        f2 = st.number_input("KM Atual do Painel", value=100000.0)
        if st.form_submit_button("SALVAR E ABRIR MEU PAINEL"):
            cursor.execute("INSERT INTO veiculo VALUES (?,?,?,?,?,?)", (user, f2, f2+10000, 350.0, f1, 0.0))
            conn.commit(); st.rerun()
    st.stop()

# --- 4. PAINEL PRINCIPAL ---
st.title(f"🚀 PAINEL: {user.upper()}")
tab_ipva, tab_ganhos, tab_metas = st.tabs(["📊 RESUMO & IPVA", "💰 MEUS GANHOS", "🎯 MINHAS CAIXINHAS"])

# ABA IPVA
with tab_ipva:
    fipe, guardado_ipva = v_data[4], v_data[5]
    total_ipva = fipe * 0.04
    st.subheader("📌 Gestão Financeira IPVA")
    c1, c2, c3 = st.columns(3)
    c1.metric("IPVA Total (4%)", f"R$ {total_ipva:.2f}")
    c2.metric("Já Guardado", f"R$ {guardado_ipva:.2f}")
    c3.metric("Falta Guardar", f"R$ {total_ipva - guardado_ipva:.2f}")
    
    val_ipva = st.number_input("Valor da Operação (R$):", value=0.0, key="val_ipva")
    col_a, col_b, col_c = st.columns(3)
    if col_a.button("📥 DEPOSITAR"):
        cursor.execute("UPDATE veiculo SET guardado_ipva = guardado_ipva + ? WHERE usuario=?", (val_ipva, user))
        conn.commit(); st.rerun()
    if col_b.button("📤 RETIRAR"):
        cursor.execute("UPDATE veiculo SET guardado_ipva = guardado_ipva - ? WHERE usuario=?", (val_ipva, user))
        conn.commit(); st.rerun()
    if col_c.button("🗑️ ZERAR IPVA", key="del_ipva"):
        cursor.execute("UPDATE veiculo SET guardado_ipva = 0 WHERE usuario=?", (user,))
        conn.commit(); st.rerun()

# ABA GANHOS
with tab_ganhos:
    with st.form("form_ganhos", clear_on_submit=True):
        st.subheader("Gravar Trabalho Diário")
        g, gst, k = st.columns(3)
        v_g = g.number_input("Ganho Bruto do Dia")
        v_gst = gst.number_input("Gasto Gás/Alimentação")
        v_k = k.number_input("KM Rodados")
        if st.form_submit_button("💾 SALVAR JORNADA"):
            cursor.execute("INSERT INTO ganhos (usuario, data, ganho, gasto, km, h_ini, h_fim) VALUES (?,?,?,?,?,?,?)", 
                           (user, str(hoje), v_g, v_gst, v_k, "08:00", "18:00"))
            conn.commit(); st.success("Gravado!"); st.rerun()

    st.subheader("📜 Histórico Recente")
    df_g = pd.read_sql_query(f"SELECT * FROM ganhos WHERE usuario='{user}' ORDER BY id DESC", conn)
    for i, r in df_g.iterrows():
        with st.container():
            col_txt, col_del = st.columns([5, 1])
            col_txt.write(f"📅 **{r['data']}** | Lucro: **R$ {r['ganho']-r['gasto']:.2f}** | KM: {r['km']}")
            if col_del.button("🗑️", key=f"del_g_{r['id']}"):
                cursor.execute("DELETE FROM ganhos WHERE id=?", (r['id'],))
                conn.commit(); st.rerun()

# ABA CAIXINHAS
with tab_metas:
    st.subheader("🎯 Suas Metas e Sonhos")
    with st.expander("➕ ADICIONAR NOVO SONHO"):
        with st.form("meta_sonho"):
            it = st.text_input("Qual o objetivo?"); v = st.number_input("Valor Necessário R$")
            if st.form_submit_button("CRIAR CAIXINHA"):
                cursor.execute("INSERT INTO metas (usuario, item, valor, data, guardado) VALUES (?,?,?,?,?)", 
                               (user, it, v, str(hoje), 0.0))
                conn.commit(); st.rerun()

    metas_db = pd.read_sql_query(f"SELECT * FROM metas WHERE usuario='{user}'", conn)
    for i, m in metas_db.iterrows():
        with st.container():
            st.write(f"### 🚀 {m['item']}")
            ja_meta = m['guardado'] or 0.0
            st.progress(min(ja_meta / m['valor'], 1.0) if m['valor'] > 0 else 0)
            st.write(f"Guardado: **R$ {ja_meta:.2f}** / Meta: R$ {m['valor']:.2f}")
            
            v_mov = st.number_input("Valor da Operação:", key=f"val_m_{m['id']}", value=0.0)
            c1, c2, c3 = st.columns(3)
            if c1.button("📥 DEPOSITAR", key=f"in_m_{m['id']}"):
                cursor.execute("UPDATE metas SET guardado = guardado + ? WHERE id=?", (v_mov, m['id']))
                conn.commit(); st.rerun()
            if c2.button("📤 RETIRAR", key=f"out_m_{m['id']}"):
                cursor.execute("UPDATE metas SET guardado = guardado - ? WHERE id=?", (v_mov, m['id']))
                conn.commit(); st.rerun()
            if c3.button("🗑️ APAGAR", key=f"del_m_{m['id']}"):
                cursor.execute("DELETE FROM metas WHERE id=?", (m['id'],))
                conn.commit(); st.rerun()

# BARRA LATERAL
st.sidebar.title("⚙️ CONFIGURAÇÕES")
if st.sidebar.button("🚪 SAIR DO APP"):
    st.session_state.autenticado = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("ZONA DE PERIGO")
if st.sidebar.button("⚠️ ZERAR TODOS OS MEUS DADOS"):
    cursor.execute("DELETE FROM ganhos WHERE usuario=?", (user,))
    cursor.execute("DELETE FROM metas WHERE usuario=?", (user,))
    cursor.execute("DELETE FROM veiculo WHERE usuario=?", (user,))
    conn.commit()
    st.rerun()
