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
        u = st.text_input("Usuário", key="login_user").strip().lower()
        s = st.text_input("Senha", type="password", key="login_pass").strip()
        if st.button("Entrar no Painel", use_container_width=True):
            sucesso = False
            for index, row in df_usuarios.iterrows():
                if str(row['usuario']).lower() == u and str(row['senha']) == s:
                    sucesso = True
                    break
            if sucesso:
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
        df_dados = pd.DataFrame(columns=["Data", "Ganho", "Gasto", "KM", "H_Inicio", "H_Fim"])

    # --- FORMULÁRIO DE LANÇAMENTO ---
    with st.container(border=True):
        st.subheader("🎯 Configuração Diária")
        
        nova_meta = st.number_input("Sua Meta Diária (R$)", min_value=0.0, value=meta_atual, step=10.0)
        if nova_meta != meta_atual:
            with open(arq_meta, "w") as f:
                f.write(str(nova_meta))
            st.rerun()

        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        g = c1.number_input("Ganho Bruto (R$)", min_value=0.0, step=1.0)
        p = c2.number_input("Gasto (R$)", min_value=0.0, step=1.0)
        km = c3.number_input("KM Rodado", min_value=0.0, step=1.0)
        
        ch1, ch2 = st.columns(2)
        h_ini = ch1.time_input("Horário de Início", value=time(6, 0))
        h_fim = ch2.time_input("Horário de Término", value=time(11, 0))
        
        if st.button("➕ SALVAR REGISTRO", use_container_width=True, type="primary"):
            hoje_data = date.today().strftime("%d/%m/%Y")
            nova_linha = pd.DataFrame({
                "Data": [hoje_data], 
                "Ganho": [g], 
                "Gasto": [p], 
                "KM": [km],
                "H_Inicio": [h_ini.strftime("%H:%M")],
                "H_Fim": [h_fim.strftime("%H:%M")]
            })
            df_dados = pd.concat([df_dados, nova_linha], ignore_index=True)
            df_dados.to_csv(arq_dados, index=False)
            st.success("Gravado!")
            st.rerun()

    # --- CÁLCULOS E RESULTADOS ---
    hoje_str = date.today().strftime("%d/%m/%Y")
    df_hoje = df_dados[df_dados['Data'] == hoje_str]
    
    total_bruto = df_hoje['Ganho'].sum()
    total_km = df_hoje['KM'].sum()
    saldo_hoje = total_bruto - df_hoje['Gasto'].sum()
    valor_por_km = total_bruto / total_km if total_km > 0 else 0

    # Cálculo de Horas Trabalhadas e Valor/Hora
    total_horas_decimal = 0
    for _, row in df_hoje.iterrows():
        try:
            t1 = datetime.strptime(row['H_Inicio'], "%H:%M")
            t2 = datetime.strptime(row['H_Fim'], "%H:%M")
            diff = (t2 - t1).total_seconds() / 3600
            if diff < 0: diff += 24 # Caso vire a noite
            total_horas_decimal += diff
        except:
            pass
    
    valor_por_hora = total_bruto / total_horas_decimal if total_horas_decimal > 0 else 0

    if nova_meta > 0:
        cor = "#28a745" if saldo_hoje >= nova_meta else "#dc3545"
        txt = "✅ META BATIDA!" if saldo_hoje >= nova_meta else "❌ AINDA ABAIXO DA META"
    else:
        cor, txt = "#444444", "🎯 DEFINE UMA META ACIMA"

    st.markdown(f"""
        <div style="background-color: {cor}; padding: 25px; border-radius: 15px; text-align: center; color: white; margin-bottom: 20px;">
            <p style="margin: 0; opacity: 0.8;">Saldo Líquido de Hoje</p>
            <h1 style="margin: 0; font-size: 3em;">R$ {saldo_hoje:.2f}</h1>
            <p style="font-weight: bold; font-size: 1.1em; margin-top: 10px;">{txt}</p>
        </div>
    """, unsafe_allow_html=True)

    # Métricas de Eficiência
    m1, m2, m3 = st.columns(3)
    m1.metric("KM Hoje", f"{total_km:.1f} km")
    m2.metric("R$ / KM", f"R$ {valor_por_km:.2f}")
    m3.metric("R$ / Hora", f"R$ {valor_por_hora:.2f}")

    # --- HISTÓRICO ---
    if not df_dados.empty:
        st.markdown("---")
        st.write("### 📜 Histórico Recente")
        
        for i, row in df_dados.iloc[::-1].head(10).iterrows():
            with st.container(border=True):
                col_info, col_valores, col_del = st.columns([1.5, 2, 0.4])
                
                with col_info:
                    st.write(f"📅 **{row['Data']}**")
                    st.write(f"⏰ {row['H_Inicio']} às {row['H_Fim']}")
                
                with col_valores:
                    lucro = float(row['Ganho']) - float(row['Gasto'])
                    st.write(f"💰 Lucro: **R$ {lucro:.2f}** (Bruto: R$ {row['Ganho']:.2f})")
                    st.write(f"🚗 {row['KM']} km")
                
                if col_del.button("🗑️", key=f"del_{i}"):
                    df_dados = df_dados.drop(i)
                    df_dados.to_csv(arq_dados, index=False)
                    st.rerun()
else:
    tela_acesso()
