import streamlit as st
import json
import os
from datetime import date

st.set_page_config(page_title="Controle Diário", layout="centered")

ARQUIVO = "dados.json"

# ------------------ FUNÇÕES ------------------

def carregar_dados():
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, "r") as f:
            return json.load(f)
    return {}

def salvar_dados(dados):
    with open(ARQUIVO, "w") as f:
        json.dump(dados, f)

# ------------------ INICIALIZAÇÃO ------------------

dados = carregar_dados()
hoje = str(date.today())

if hoje not in dados:
    dados[hoje] = {"gastos": [], "ganhos": []}

# ------------------ RESUMO TOPO ------------------

total_gastos = sum(dados[hoje]["gastos"])
total_ganhos = sum(dados[hoje]["ganhos"])
liquido = total_ganhos - total_gastos

st.title("💰 Controle Diário")

col1, col2, col3 = st.columns(3)
col1.metric("💵 Bruto", f"R$ {total_ganhos:.2f}")
col2.metric("💸 Gastos", f"R$ {total_gastos:.2f}")
col3.metric("✅ Líquido", f"R$ {liquido:.2f}")

st.divider()

# ------------------ GASTOS ------------------

st.subheader("📉 Gastos")

categorias_gastos = ["Luz", "Água", "Alimentação", "Combustível", "Outros"]

cols = st.columns(len(categorias_gastos))

for i, cat in enumerate(categorias_gastos):
    if cols[i].button(cat):
        st.session_state.tipo_gasto = cat

if "tipo_gasto" in st.session_state:
    valor = st.number_input(f"Valor para {st.session_state.tipo_gasto}:", min_value=0.0)

    if st.button("Confirmar Gasto"):
        dados[hoje]["gastos"].append(valor)
        salvar_dados(dados)
        st.success("Gasto adicionado!")
        del st.session_state.tipo_gasto
        st.rerun()

# ------------------ GANHOS ------------------

st.subheader("📈 Ganhos")

categorias_ganhos = ["Corrida", "Hora", "Extra", "Caixinha", "Outros"]

cols = st.columns(len(categorias_ganhos))

for i, cat in enumerate(categorias_ganhos):
    if cols[i].button(cat):
        st.session_state.tipo_ganho = cat

if "tipo_ganho" in st.session_state:
    valor = st.number_input(f"Valor para {st.session_state.tipo_ganho}:", min_value=0.0, key="ganho")

    if st.button("Confirmar Ganho"):
        dados[hoje]["ganhos"].append(valor)
        salvar_dados(dados)
        st.success("Ganho adicionado!")
        del st.session_state.tipo_ganho
        st.rerun()

# ------------------ AÇÕES RÁPIDAS ------------------

st.subheader("⚙️ Ajustes rápidos")

col1, col2 = st.columns(2)

if col1.button("↩️ Apagar último GASTO"):
    if dados[hoje]["gastos"]:
        dados[hoje]["gastos"].pop()
        salvar_dados(dados)
        st.warning("Último gasto removido!")
        st.rerun()

if col2.button("↩️ Apagar último GANHO"):
    if dados[hoje]["ganhos"]:
        dados[hoje]["ganhos"].pop()
        salvar_dados(dados)
        st.warning("Último ganho removido!")
        st.rerun()

# ------------------ HISTÓRICO ------------------

st.subheader("📅 Histórico")

for dia in sorted(dados.keys(), reverse=True):
    tg = sum(dados[dia]["ganhos"])
    tgastos = sum(dados[dia]["gastos"])
    liquido = tg - tgastos

    st.write(f"📆 {dia} | 💵 {tg:.2f} | 💸 {tgastos:.2f} | ✅ {liquido:.2f}")
