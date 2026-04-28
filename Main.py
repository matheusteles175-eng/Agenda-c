import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Calculadora do Motorista", page_icon="🚖", layout="centered")

ARQUIVO_USUARIOS = "usuarios.csv"

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        return pd.read_csv(ARQUIVO_USUARIOS, dtype=str)
    else:
        df = pd.DataFrame([{"usuario": "matheus", "senha": "123"}])
        df.to_csv(ARQUIVO_USUARIOS, index=False)
        return df

# Inicialização de variáveis de memória (Essencial para não perder dados ao atualizar a tela)
if "logado" not in st.session_state:
    st.session_state.logado = False
if "corridas_atuais" not in st.session_state:
    st.session_state.corridas_atuais = []

def tela_acesso():
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>🚖 Sistema de Ganhos</h1>", unsafe_allow_html=True)
    aba1, aba2 = st.tabs(["Entrar", "Criar Conta"])
    df_usuarios = carregar_usuarios()

    with aba1:
        u = st.text_input("Usuário", key="login_user").strip()
        s = st.text_input("Senha", type="password", key="login_pass").strip()
        if st.button("Entrar no Painel", use_container_width=True):
            sucesso = any((str(row['usuario']).lower() == u.lower() and str(row['senha']) == s) for _, row in df_usuarios.iterrows())
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
    usuario_path = st.session_state.usuario_atual.lower()
    arq_dados = f"dados_{usuario_path}.csv"
    arq_meta = f"meta_{usuario_path}.txt"

    # Carregar Meta Salva
    if os.path.exists(arq_meta):
        with open(arq_meta, "r") as f:
            try: meta_atual = float(f.read())
            except: meta_atual = 0.0
    else:
        meta_atual = 0.0

    st.sidebar.write(f"👤 Motorista: **{st.session_state.usuario_atual.capitalize()}**")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.session_state.corridas_atuais = []
        st.rerun()

    st.title(f"📊 Painel de Turno Ativo")

    # --- CONTROLE DE HORAS ---
    with st.expander("🕒 Horário de Trabalho", expanded=True):
        col_ini, col_fim = st.columns(2)
        # Define o padrão para agora, mas permite ajustar
        hora_inicio = col_ini.time_input("Início do Turno", value=datetime.now().replace(hour=7, minute=0))
        hora_fim = col_fim.time_input("Fim do Turno (Agora)", value=datetime.now().time())

    # --- CALCULADORA PARCIAL ---
    with st.container(border=True):
        st.subheader("➕ Adicionar Ganho/Gasto")
        col_g, col_p = st.columns(2)
        g_parcial = col_g.number_input("Valor Bruto (R$)", min_value=0.0, step=0.50, key="input_ganho")
        p_parcial = col_p.number_input("Gasto/Taxa (R$)", min_value=0.0, step=0.50, key="input_gasto")
        
        if st.button("REGISTRAR NA SOMA PARCIAL", use_container_width=True):
            if g_parcial > 0 or p_parcial > 0:
                st.session_state.corridas_atuais.append({"ganho": g_parcial, "gasto": p_parcial})
                st.toast(f"Adicionado: +R${g_parcial:.2f}")
            else:
                st.warning("Insira um valor para somar.")

    # --- PROCESSAMENTO DOS DADOS DO TURNO ---
    ganho_bruto_atual = sum(item['ganho'] for item in st.session_state.corridas_atuais)
    gasto_total_atual = sum(item['gasto'] for item in st.session_state.corridas_atuais)
    saldo_atual = ganho_bruto_atual - gasto_total_atual

    # Cálculo de Horas para Média
    t1 = datetime.combine(date.today(), hora_inicio)
    t2 = datetime.combine(date.today(), hora_fim)
    total_segundos = (t2 - t1).total_seconds()
    delta_horas = total_segundos / 3600 if total_segundos > 0 else 1
    ganho_por_hora = ganho_bruto_atual / delta_horas

    # Painel Visual de Metas e Status
    if meta_atual > 0:
        cor_fundo = "#28a745" if saldo_atual >= meta_atual else "#dc3545"
        status_txt = "✅ META BATIDA!" if saldo_atual >= meta_atual else "❌ BUSCANDO A META"
    else:
        cor_fundo = "#444444"
        status_txt = "META NÃO DEFINIDA"

    st.markdown(f"""
        <div style="background-color: {cor_fundo}; padding: 25px; border-radius: 15px; color: white; margin-bottom: 20px; text-align: center;">
            <div style="display: flex; justify-content: space-around;">
                <div><small>GANHO BRUTO</small><br><b style="font-size: 1.2em;">R$ {ganho_bruto_atual:.2f}</b></div>
                <div><small>GASTO TOTAL</small><br><b style="font-size: 1.2em;">R$ {gasto_total_atual:.2f}</b></div>
                <div><small>LUCRO LÍQUIDO</small><br><b style="font-size: 1.8em;">R$ {saldo_atual:.2f}</b></div>
            </div>
            <hr style="border: 0.5px solid rgba(255,255,255,0.2);">
            <p style="margin: 0; font-weight: bold;">{status_txt} | Média: R$ {ganho_por_hora:.2f}/h</p>
        </div>
    """, unsafe_allow_html=True)

    # Configuração de Meta (dentro de um expander para não ocupar espaço)
    with st.expander("⚙️ Ajustar Meta Diária"):
        nova_meta = st.number_input("Sua Meta (R$)", min_value=0.0, value=meta_atual, step=10.0)
        if st.button("Salvar Nova Meta"):
            with open(arq_meta, "w") as f:
                f.write(str(nova_meta))
            st.rerun()

    # --- FECHAMENTO DO DIA ---
    st.markdown("###")
    if st.button("🏁 FECHAR DIA E SALVAR PLANILHA", use_container_width=True, type="primary"):
        if st.session_state.corridas_atuais:
            hoje_data = date.today().strftime("%d/%m/%Y")
            nova_linha = pd.DataFrame({
                "Data": [hoje_data], 
                "Ganho_Bruto": [ganho_bruto_atual], 
                "Gasto_Total": [gasto_total_atual],
                "Lucro_Liquido": [saldo_atual],
                "Média_Hora": [round(ganho_por_hora, 2)]
            })
            
            if os.path.exists(arq_dados):
                df_hist = pd.read_csv(arq_dados)
                df_hist = pd.concat([df_hist, nova_linha], ignore_index=True)
            else:
                df_hist = nova_linha
                
            df_hist.to_csv(arq_dados, index=False)
            st.session_state.corridas_atuais = [] # Zera a calculadora para o próximo turno
            st.success("Turno finalizado e guardado no histórico!")
            st.balloons()
            st.rerun()
        else:
            st.error("Não há registros para fechar o dia.")

    # --- VISUALIZAÇÃO DO HISTÓRICO ---
    st.markdown("---")
    st.subheader("📜 Histórico de Dias Anteriores")
    if os.path.exists(arq_dados):
        df_visual = pd.read_csv(arq_dados)
        st.dataframe(df_visual.iloc[::-1], use_container_width=True) # Mostra o mais recente primeiro
    else:
        st.info("Nenhum dia fechado no histórico.")

else:
    tela_acesso()
