import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, time

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

if "logado" not in st.session_state:
    st.session_state.logado = False

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_rascunho(lista, h_ini, h_fim, usuario):
    # Salva as corridas e os horários para não resetar
    dados = {
        "corridas": lista,
        "hora_inicio": h_ini.strftime("%H:%M"),
        "hora_fim": h_fim.strftime("%H:%M")
    }
    import json
    with open(f"rascunho_{usuario}.json", "w") as f:
        json.dump(dados, f)

def carregar_rascunho(usuario):
    arq = f"rascunho_{usuario}.json"
    if os.path.exists(arq):
        import json
        try:
            with open(arq, "r") as f:
                dados = json.load(f)
                # Converte string de volta para objeto time
                h_ini = datetime.strptime(dados["hora_inicio"], "%H:%M").time()
                h_fim = datetime.strptime(dados["hora_fim"], "%H:%M").time()
                return dados["corridas"], h_ini, h_fim
        except:
            return [], time(7, 0), datetime.now().time()
    return [], time(7, 0), datetime.now().time()

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
                st.session_state.usuario_atual = u.lower()
                # Carrega tudo do rascunho
                corridas, h_i, h_f = carregar_rascunho(u.lower())
                st.session_state.corridas_atuais = corridas
                st.session_state.h_ini = h_i
                st.session_state.h_fim = h_f
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with aba2:
        novo_u = st.text_input("Novo Usuário", key="cad_user").strip()
        novo_s = st.text_input("Nova Senha", type="password", key="cad_pass").strip()
        if st.button("Criar Minha Conta", use_container_width=True):
            if novo_u == "" or novo_s == "": st.error("Preencha todos os campos!")
            else:
                novo_reg = pd.DataFrame([{"usuario": novo_u, "senha": str(novo_s)}])
                pd.concat([df_usuarios, novo_reg], ignore_index=True).to_csv(ARQUIVO_USUARIOS, index=False)
                st.success("Conta criada!")

if st.session_state.logado:
    user = st.session_state.usuario_atual
    arq_dados = f"dados_{user}.csv"
    arq_meta = f"meta_{user}.txt"
    arq_rascunho_json = f"rascunho_{user}.json"

    # Inicializa variáveis se não existirem
    if "corridas_atuais" not in st.session_state:
        corridas, h_i, h_f = carregar_rascunho(user)
        st.session_state.corridas_atuais = corridas
        st.session_state.h_ini = h_i
        st.session_state.h_fim = h_f

    # Carregar Meta
    if os.path.exists(arq_meta):
        with open(arq_meta, "r") as f:
            try: meta_atual = float(f.read())
            except: meta_atual = 0.0
    else: meta_atual = 0.0

    st.sidebar.write(f"👤 Motorista: **{user.capitalize()}**")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    st.title(f"📊 Painel de Turno")

    # --- CONTROLE DE HORAS ---
    with st.expander("🕒 Horário de Trabalho", expanded=True):
        col_ini, col_fim = st.columns(2)
        # O valor agora vem do session_state para não resetar
        nova_h_ini = col_ini.time_input("Início do Turno", value=st.session_state.h_ini)
        nova_h_fim = col_fim.time_input("Fim do Turno", value=st.session_state.h_fim)
        
        # Se você mudar o horário na tela, ele salva no rascunho
        if nova_h_ini != st.session_state.h_ini or nova_h_fim != st.session_state.h_fim:
            st.session_state.h_ini = nova_h_ini
            st.session_state.h_fim = nova_h_fim
            salvar_rascunho(st.session_state.corridas_atuais, nova_h_ini, nova_h_fim, user)

    # --- CALCULADORA PARCIAL ---
    with st.container(border=True):
        st.subheader("➕ Adicionar Corrida")
        c1, c2 = st.columns(2)
        g_p = c1.number_input("Ganho (R$)", min_value=0.0, step=0.50)
        p_p = c2.number_input("Gasto (R$)", min_value=0.0, step=0.50)
        
        if st.button("REGISTRAR PARCIAL", use_container_width=True):
            if g_p > 0 or p_p > 0:
                st.session_state.corridas_atuais.append({"ganho": g_p, "gasto": p_p})
                salvar_rascunho(st.session_state.corridas_atuais, st.session_state.h_ini, st.session_state.h_fim, user)
                st.toast("Adicionado!")
                st.rerun()

    # --- CÁLCULOS ---
    bruto = sum(i['ganho'] for i in st.session_state.corridas_atuais)
    gastos = sum(i['gasto'] for i in st.session_state.corridas_atuais)
    liquido = bruto - gastos

    t1 = datetime.combine(date.today(), st.session_state.h_ini)
    t2 = datetime.combine(date.today(), st.session_state.h_fim)
    diff = (t2 - t1).total_seconds()
    horas = diff / 3600 if diff > 0 else 1
    media = bruto / horas

    # Painel Visual
    cor = "#444444"
    if meta_atual > 0:
        cor = "#28a745" if liquido >= meta_atual else "#dc3545"

    st.markdown(f"""
        <div style="background-color: {cor}; padding: 20px; border-radius: 15px; color: white; text-align: center;">
            <div style="display: flex; justify-content: space-around;">
                <div><small>BRUTO</small><br><b>R$ {bruto:.2f}</b></div>
                <div><small>GASTOS</small><br><b>R$ {gastos:.2f}</b></div>
                <div><small>LUCRO</small><br><b style="font-size: 1.5em;">R$ {liquido:.2f}</b></div>
            </div>
            <p style="margin-top: 10px;">Média: R$ {media:.2f}/h</p>
        </div>
    """, unsafe_allow_html=True)

    # --- FECHAMENTO ---
    st.markdown("###")
    if st.button("🏁 FECHAR DIA E SALVAR", use_container_width=True, type="primary"):
        if st.session_state.corridas_atuais:
            nova_linha = pd.DataFrame({
                "Data": [date.today().strftime("%d/%m/%Y")], 
                "Ganho_Bruto": [bruto], "Gasto_Total": [gastos],
                "Lucro_Liquido": [liquido], "Média_Hora": [round(media, 2)]
            })
            df_hist = pd.read_csv(arq_dados) if os.path.exists(arq_dados) else pd.DataFrame()
            pd.concat([df_hist, nova_linha], ignore_index=True).to_csv(arq_dados, index=False)
            
            # Limpa rascunho
            st.session_state.corridas_atuais = []
            if os.path.exists(arq_rascunho_json): os.remove(arq_rascunho_json)
            st.success("Dia Salvo!")
            st.balloons()
            st.rerun()

    # Histórico
    if os.path.exists(arq_dados):
        st.write("---")
        st.dataframe(pd.read_csv(arq_dados).iloc[::-1], use_container_width=True)

else:
    tela_acesso()
            
