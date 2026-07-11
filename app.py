import streamlit as st

st.set_page_config(page_title="E-commerce Reviews", page_icon="⭐")

st.title("Análise de Reviews")
produto = st.text_input("Nome do produto")

if st.button("Analisar"):
    if produto:
        st.success(f"Analisando reviews de: {produto}")
        st.write("Aqui você pode exibir gráficos, métricas e o resumo gerado pelo seu pipeline.")
    else:
        st.warning("Digite o nome de um produto.")