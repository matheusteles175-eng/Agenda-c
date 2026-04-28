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

if "logado" not in st.session_state:
    st.session_state.logado = False

# --- FUNÇÕES DE PERSISTÊNCIA DO RASCUNHO (MEMÓRIA PERMANENTE) ---
def salvar_rascunho(lista, usuario):
    df = pd.DataFrame(lista)
    df.to_csv(f"rascunho_{usuario}.csv", index=False)

def carregar_rascunho(usuario):
    arq = f"rascunho_{usuario}.csv"
    if os.path.exists(arq):
        try:
            return pd.read_csv(arq).to_dict('records')
        except:
            return []
    return []

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
                # Carrega o rascunho salvo anteriormente ao logar
                st.session_state.corridas_atuais = carregar_rascunho(u.lower())
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
    usuario_path = st.session_state.usuario_atual
    arq_dados = f"dados_{usuario_path}.csv"
    arq_meta = f"meta_{usuario_path}.txt"
    arq_rascunho = f"rascunho_{usuario_path}.csv"

    # Se por algum motivo a lista não estiver no session_state, tenta carregar do arquivo
    if "corridas_atuais" not in st.session_state:
        st.session_state.corridas_atuais = carregar_rascunho(usuario_path)

    # Carregar Meta
    if os.path.exists(arq_meta):
        with open(arq_meta, "r") as f:
            try: meta_atual = float(f.read())
            except: meta_atual = 0.0
    else:
        meta_atual = 0.0

    st.sidebar.write(f"👤 Motorista: **{usuario_path.capitalize()}**")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    st.title(f"📊 Painel de Turno Ativo")

    # --- CONTROLE DE HORAS ---
    with st.expander("🕒 Horário de Trabalho", expanded=True):
        col_ini, col_fim = st.columns(2)
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
                # Adiciona na memória E salva no arquivo de rascunho imediatamente
                st.session_state.corridas_atuais.append({"ganho": g_parcial, "gasto": p_parcial})
                salvar_rascunho(st.session_state.corridas_atuais, usuario_path)
                st.toast(f"Adicionado: +R${g_parcial:.2f}")
                st.rerun()
            else:
                st.warning("Insira um valor para somar.")

    # --- CÁLCULOS ---
    ganho_bruto_total = sum(item['ganho'] for item in st.session_state.corridas_atuais)
    gasto_total_acumulado = sum(item['gasto'] for item in st.session_state.corridas_atuais)
    saldo_liquido = ganho_bruto_total - gasto_total_acumulado

    t1 = datetime.combine(date.today(), hora_inicio)
    t2 = datetime.combine(date.today(), hora_fim)
    total_segundos = (t2 - t1).total_seconds()
    delta_horas = total_segundos / 3600 if total_segundos > 0 else 1
    ganho_por_hora = ganho_bruto_total / delta_horas

    # Painel Visual
    cor_fundo = "#444444"
    status_txt = "META NÃO DEFINIDA"
    if meta_atual > 0:
        cor_fundo = "#28a745" if saldo_liquido >= meta_atual else "#dc3545"
        status_txt = "✅ META BATIDA!" if saldo_liquido >= meta_atual else "❌ BUSCANDO A META"

    st.markdown(f"""
        <div style="background-color: {cor_fundo}; padding: 25px; border-radius: 15px; color: white; margin-bottom: 20px; text-align: center;">
            <div style="display: flex; justify-content: space-around;">
                <div><small>GANHO BRUTO</small><br><b style="font-size: 1.2em;">R$ {ganho_bruto_total:.2f}</b></div>
                <div><small>GASTO TOTAL</small><br><b style="font-size: 1.2em;">R$ {gasto_total_acumulado:.2f}</b></div>
                <div><small>LUCRO LÍQUIDO</small><br><b style="font-size: 1.8em;">R$ {saldo_liquido:.2f}</b></div>
            </div>
            <hr style="border: 0.5px solid rgba(255,255,255,0.2);">
            <p style="margin: 0; font-weight: bold;">{status_txt} | Média: R$ {ganho_por_hora:.2f}/h</p>
        </div>
    """, unsafe_allow_html=True)

    # --- BOTÕES DE AÇÃO ---
    col_meta, col_limpar = st.columns(2)
    with col_meta:
        with st.popover("⚙️ Ajustar Meta"):
            nova_meta = st.number_input("Sua Meta", min_value=0.0, value=meta_atual)
            if st.button("Salvar Meta"):
                with open(arq_meta, "w") as f: f.write(str(nova_meta))
                st.rerun()
    
    with col_limpar:
        if st.button("🗑️ Resetar Parciais", use_container_width=True):
            st.session_state.corridas_atuais = []
            if os.path.exists(arq_rascunho): os.remove(arq_rascunho)
            st.rerun()

    st.markdown("###")
    if st.button("🏁 FECHAR DIA E SALVAR PLANILHA", use_container_width=True, type="primary"):
        if st.session_state.corridas_atuais:
            hoje_data = date.today().strftime("%d/%m/%Y")
            nova_linha = pd.DataFrame({
                "Data": [hoje_data], 
                "Ganho_Bruto": [ganho_bruto_total], 
                "Gasto_Total": [gasto_total_acumulado],
                "Lucro_Liquido": [saldo_liquido],
                "Média_Hora": [round(ganho_por_hora, 2)]
            })
            
            df_hist = pd.read_csv(arq_dados) if os.path.exists(arq_dados) else pd.DataFrame()
            pd.concat([df_hist, nova_linha], ignore_index=True).to_csv(arq_dados, index=False)
            
            # Limpa tudo após fechar o dia
            st.session_state.corridas_atuais = []
            if os.path.exists(arq_rascunho): os.remove(arq_rascunho)
            st.success("Dia fechado e rascunho limpo!")
            st.balloons()
            st.rerun()

    # Histórico
    st.markdown("---")
    if os.path.exists(arq_dados):
        st.write("### 📜 Histórico de Dias")
        st.dataframe(pd.read_csv(arq_dados).iloc[::-1], use_container_width=True)

else:
    tela_acesso()
