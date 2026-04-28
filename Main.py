import streamlit as st
import pandas as pd
import os
from datetime import date, time, datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Calculadora de Ganhos 🚖", page_icon="🚖", layout="centered")

ARQUIVO_USUARIOS = "usuarios.csv"

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        return pd.read_csv(ARQUIVO_USUARIOS, dtype=str)
    else:
        # Cria arquivo inicial com usuário padrão (sempre em minúsculo no CSV)
        df = pd.DataFrame([{"usuario": "matheus", "senha": "123"}])
        df.to_csv(ARQUIVO_USUARIOS, index=False)
        return df

if "logado" not in st.session_state:
    st.session_state.logado = False

def tela_acesso():
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>🚖 Sistema de Ganhos</h1>", unsafe_allow_html=True)
    aba1, aba2 = st.tabs(["Entrar", "Criar Conta"])
    df_usuarios = carregar_usuarios()

    with aba1:
        # Usamos .lower() e .strip() para evitar erros de digitação
        u = st.text_input("Usuário", key="login_user").strip().lower()
        s = st.text_input("Senha", type="password", key="login_pass").strip()
        
        if st.button("Entrar no Painel", use_container_width=True):
            # Verificação direta no DataFrame (mais segura)
            usuario_existe = df_usuarios[(df_usuarios['usuario'].str.lower() == u) & (df_usuarios['senha'] == s)]
            
            if not usuario_existe.empty:
                st.session_state.logado = True
                st.session_state.usuario_atual = u
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with aba2:
        novo_u = st.text_input("Novo Usuário", key="cad_user").strip().lower()
        novo_s = st.text_input("Nova Senha", type="password", key="cad_pass").strip()
        
        if st.button("Criar Minha Conta", use_container_width=True):
            if novo_u == "" or novo_s == "":
                st.error("Preencha todos os campos!")
            elif novo_u in df_usuarios['usuario'].str.lower().values:
                st.error("Este usuário já existe!")
            else:
                novo_reg = pd.DataFrame([{"usuario": novo_u, "senha": str(novo_s)}])
                pd.concat([df_usuarios, novo_reg], ignore_index=True).to_csv(ARQUIVO_USUARIOS, index=False)
                st.success("Conta criada! Pode fazer o login agora.")

if st.session_state.logado:
    user = st.session_state.usuario_atual
    arq_dados = f"dados_{user}.csv"
    arq_meta = f"meta_{user}.txt"

    if os.path.exists(arq_meta):
        with open(arq_meta, "r") as f:
            try: meta_atual = float(f.read())
            except: meta_atual = 0.0
    else:
        meta_atual = 0.0

    st.sidebar.write(f"👤 Motorista: **{user.capitalize()}**")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    st.title(f"📊 Gestão de Ganhos")

    if os.path.exists(arq_dados):
        df_dados = pd.read_csv(arq_dados)
        for col in ['Ganho', 'Gasto', 'KM']:
            if col not in df_dados.columns: df_dados[col] = 0.0
            df_dados[col] = pd.to_numeric(df_dados[col], errors='coerce').fillna(0.0)
        if 'H_Inicio' not in df_dados.columns: df_dados['H_Inicio'] = "00:00"
        if 'H_Fim' not in df_dados.columns: df_dados['H_Fim'] = "00:00"
    else:
        df_dados = pd.DataFrame(columns=["Data", "Ganho", "Gasto", "KM", "H_Inicio", "H_
