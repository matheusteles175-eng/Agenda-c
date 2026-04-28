import streamlit as st
import pandas as pd
import os
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Calculadora de Ganhos", page_icon="🚖", layout="centered")

ARQUIVO_USUARIOS = "usuarios.csv"

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        return pd.read_csv(ARQUIVO_USUARIOS, dtype=str)
    else:
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
        u = st.text_input("Usuário", key="login_user").strip()
        s = st.text_input("Senha", type="password", key="login_pass").strip()
        if st.button("Entrar no Painel", use_container_width=True):
            sucesso = False
            for index, row in df_usuarios.iterrows():
                if str(row['usuario']).lower() == u.lower() and str(row['senha']) == s:
                    sucesso = True
                    break
            if sucesso:
                st.session_state.logado = True
                st.session_state.usuario_atual = u
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with aba2:
        novo_u = st.text_input("Novo Usuário", key="cad_user").strip()
        novo_s = st.text_input("Nova Senha", type="password", key="cad_pass").strip()
        if st.button("Criar Minha Conta", use_container_width=True):
            if novo_u == "" or novo_s == "":
                st.error("Preencha todos os campos!")
            elif novo_u.lower() in df_usuarios['usuario'].str.lower().values:
                st.error("Este usuário já existe!")
            else:
                novo_reg = pd.DataFrame([{"usuario": novo_u, "senha": str(novo_s)}])
                pd.concat([df_usuarios, novo_reg], ignore_index=True).to_csv(ARQUIVO_USUARIOS, index=False)
                st.success("Conta criada!")

if st.session_state.logado:
    # --- DADOS DO USUÁRIO ---
    st.sidebar.markdown(f"### 👤 {st.session_state.usuario_atual.capitalize()}")
    
    arq_dados = f"dados_{st.session_state.usuario_atual.lower()}.csv"
    arq_meta = f"meta_{st.session_state.usuario_atual.lower()}.txt" # Arquivo para salvar a meta individual

    # Carregar a meta salva ou definir 0.0 se não existir
    if os.path.exists(arq_meta):
        with open(arq_meta, "r") as f:
            meta_salva = float(f.read())
    else:
        meta_salva = 0.0

    # --- CAMPO DE META NA BARRA LATERAL ---
    st.sidebar.markdown("---")
    nova_meta = st.sidebar.number_input("🎯 Defina sua Meta (R$)", min_value=0.0, value=meta_salva, step=10.0)
    
    # Se o usuário mudar a meta, a gente salva no arquivo .txt
    if nova_meta != meta_salva:
        with open(arq_meta, "w") as f:
            f.write(str(nova_meta))
        st.rerun()

    if st.sidebar.button("Sair do Sistema"):
        st.session_state.logado = False
        st.rerun()

    st.title(f"📊 Painel de Controle")
    
    df_dados = pd.read_csv(arq_dados) if os.path.exists(arq_dados) else pd.DataFrame(columns=["Data", "Ganho", "Gasto"])

    # --- FORMULÁRIO DE LANÇAMENTO ---
    with st.container(border=True):
        st.subheader("📝 Novo Lançamento")
        col_g, col_p = st.columns(2)
        with col_g:
            g = st.number_input("Ganho (R$)", min_value=0.0, step=10.0, key="input_ganho")
        with col_p:
            p = st.number_input("Gasto (R$)", min_value=0.0, step=10.0, key="input_gasto")
        
        if st.button("➕ SALVAR REGISTRO", use_container_width=True, type="primary"):
            nova_linha = pd.DataFrame({"Data": [date.today().strftime("%d/%m/%Y")], "Ganho": [g], "Gasto": [p]})
            df_dados = pd.concat([df_dados, nova_linha], ignore_index=True)
            df_dados.to_csv(arq_dados, index=False)
            st.success("Dados gravados!")
            st.rerun()

    # --- MÉTRICAS COM LÓGICA DE META ---
    if not df_dados.empty:
        hoje = date.today().strftime("%d/%m/%Y")
        df_hoje = df_dados[df_dados['Data'] == hoje]
        
        ganho_hoje = df_hoje['Ganho'].sum()
        gasto_hoje = df_hoje['Gasto'].sum()
        saldo_hoje = ganho_hoje - gasto_hoje
        
        # Só ativa a cor se a meta for maior que zero
        if nova_meta > 0:
            cor_meta = "#28a745" if saldo_hoje >= nova_meta else "#dc3545"
            label_meta = "✅ META ATINGIDA!" if saldo_hoje >= nova_meta else "❌ ABAIXO DA META"
            meta_info = f"(Meta: R$ {nova_meta:.2f})"
        else:
            cor_meta = "#333" # Cinza se não tiver meta
            label_meta
  
