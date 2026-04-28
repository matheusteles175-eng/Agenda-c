import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import date

# --- FUNÇÕES DE UTILIDADE ---
def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def carregar_usuarios():
    if os.path.exists("usuarios.csv"):
        return pd.read_csv("usuarios.csv", dtype=str)
    return pd.DataFrame([{"usuario": "admin", "senha": hash_senha("123")}])

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Driver Dashboard", page_icon="🚖", layout="centered")

# Inicialização do estado
if "logado" not in st.session_state:
    st.session_state.logado = False

# --- TELA DE ACESSO ---
def tela_acesso():
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>🚖 Driver Flow</h1>", unsafe_allow_html=True)
    aba1, aba2 = st.tabs(["Entrar", "Criar Conta"])
    df_usuarios = carregar_usuarios()

    with aba1:
        u = st.text_input("Usuário", key="login_user").strip().lower()
        s = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Acessar Painel", use_container_width=True, type="primary"):
            hash_s = hash_senha(s)
            user_match = df_usuarios[(df_usuarios['usuario'] == u) & (df_usuarios['senha'] == hash_s)]
            
            if not user_match.empty:
                st.session_state.logado = True
                st.session_state.usuario_atual = u
                st.rerun()
            else:
                st.error("Credenciais inválidas.")

    with aba2:
        novo_u = st.text_input("Novo Usuário", key="cad_user").strip().lower()
        novo_s = st.text_input("Nova Senha", type="password", key="cad_pass")
        if st.button("Cadastrar", use_container_width=True):
            if novo_u and novo_s:
                if novo_u in df_usuarios['usuario'].values:
                    st.error("Usuário já cadastrado.")
                else:
                    novo_reg = pd.DataFrame([{"usuario": novo_u, "senha": hash_senha(novo_s)}])
                    pd.concat([df_usuarios, novo_reg], ignore_index=True).to_csv("usuarios.csv", index=False)
                    st.success("Conta criada! Volte na aba 'Entrar'.")
            else:
                st.warning("Preencha todos os campos.")

# --- PAINEL PRINCIPAL ---
if st.session_state.logado:
    user = st.session_state.usuario_atual
    arq_dados = f"dados_{user}.csv"
    arq_meta = f"meta_{user}.txt"

    # Logout no Sidebar
    st.sidebar.subheader(f"Bem-vindo, {user.capitalize()}!")
    if st.sidebar.button("Sair do Sistema"):
        st.session_state.logado = False
        st.rerun()

    # Carregar Meta
    meta_atual = 0.0
    if os.path.exists(arq_meta):
        with open(arq_meta, "r") as f:
            try: meta_atual = float(f.read())
            except: pass

    # Carregar Dados
    if os.path.exists(arq_dados):
        df_dados = pd.read_csv(arq_dados)
    else:
        df_dados = pd.DataFrame(columns=["Data", "Ganho", "Gasto"])

    st.title("📊 Gestão Financeira")

    # Coluna de Configuração
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.expander("🎯 Ajustar Meta", expanded=False):
            nova_meta = st.number_input("Meta Diária (R$)", value=meta_atual, step=10.0)
            if st.button("Atualizar Meta"):
                with open(arq_meta, "w") as f: f.write(str(nova_meta))
                st.rerun()

    with col2:
        with st.expander("➕ Novo Lançamento", expanded=False):
            g = st.number_input("Ganhos", min_value=0.0)
            p = st.number_input("Gastos", min_value=0.0)
            if st.button("Salvar"):
                hoje = date.today().strftime("%d/%m/%Y")
                novo = pd.DataFrame({"Data": [hoje], "Ganho": [g], "Gasto": [p]})
                pd.concat([df_dados, novo], ignore_index=True).to_csv(arq_dados, index=False)
                st.rerun()

    # Resumo do Dia
    hoje_str = date.today().strftime("%d/%m/%Y")
    df_hoje = df_dados[df_dados['Data'] == hoje_str]
    total_ganho = df_hoje['Ganho'].sum()
    total_gasto = df_hoje['Gasto'].sum()
    saldo_hoje = total_ganho - total_gasto

    # Visualização de Status
    status_color = "#28a745" if (meta_atual > 0 and saldo_hoje >= meta_atual) else "#dc3545"
    if meta_atual == 0: status_color = "#6c757d"

    st.markdown(f"""
        <div style="background-color: {status_color}; padding: 20px; border-radius: 10px; text-align: center; color: white; margin-bottom: 20px;">
            <small>SALDO LÍQUIDO HOJE</small>
            <h1 style="margin:0;">R$ {saldo_hoje:.2f}</h1>
            <p style="margin:0; opacity: 0.9;">{'Meta Atingida!' if (meta_atual > 0 and saldo_hoje >= meta_atual) else f'Meta: R$ {meta_atual:.2f}'}</p>
        </div>
    """, unsafe_allow_html=True)

    # Métricas Detalhadas
    c1, c2, c3 = st.columns(3)
    c1.metric("Bruto", f"R$ {total_ganho:.2f}")
    c2.metric("Despesas", f"R$ {total_gasto:.2f}", delta_color="inverse")
    progresso = (saldo_hoje / meta_atual) if meta_atual > 0 else 0
    c3.metric("Progresso", f"{min(progresso*100, 100.0):.1f}%")

    # Histórico
    if not df_dados.empty:
        st.divider()
        st.subheader("Recent History")
        for i, row in df_dados.iloc[::-1].head(10).iterrows():
            with st.container(border=True):
                col_a, col_b, col_c = st.columns([2, 2, 1])
                col_a.write(f"📅 **{row['Data']}**")
                lucro = row['Ganho'] - row['Gasto']
                col_b.write(f"💰 Lucro: :green[R$ {lucro:.2f}]" if lucro >= 0 else f"💰 Lucro: :red[R$ {lucro:.2f}]")
                if col_c.button("Excluir", key=f"del_{i}", use_container_width=True):
                    df_dados.drop(i).to_csv(arq_dados, index=False)
                    st.rerun()
else:
    tela_acesso()
