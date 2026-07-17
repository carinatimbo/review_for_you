import streamlit as st
import pandas as pd
from pathlib import Path

# Configuração da página do Streamlit
st.set_page_config(page_title="Sentimento do Produto — Gold", layout="wide")

st.title("📊 Painel de Sentimento e Aprovação de Produtos")
st.markdown("Análise consolidada de menções, polaridade de sentimento e índice de aprovação por produto.")

CAMINHO_PARQUET = Path("./datalake/gold/reviews/analise_produtos_gold.parquet")


@st.cache_data
def carregar_dados(caminho):
    """Lê o parquet bruto (nível produto + termo)."""
    if not caminho.exists():
        return pd.DataFrame()
    return pd.read_parquet(caminho)


def calcular_indice(positivas, negativas):
    total = positivas + negativas
    if total == 0:
        return 0.0
    return round((positivas / total) * 100, 1)


@st.cache_data
def agrupar_por_produto(df):
    """Consolida por PRODUTO (nível cards / visão 'Todos')."""
    df_produto = df.groupby("produto").agg(
        total_mencoes=("mencoes", "sum"),
        total_videos=("videos", "sum"),
        total_positivas=("mencoes_positivas", "sum"),
        total_negativas=("mencoes_negativas", "sum"),
    ).reset_index()

    df_produto["indice_aprovacao"] = df_produto.apply(
        lambda row: calcular_indice(row["total_positivas"], row["total_negativas"]), axis=1
    )
    return df_produto.sort_values(by="indice_aprovacao", ascending=False)


@st.cache_data
def agrupar_por_termo(df, produto):
    """Consolida por TERMO dentro de um produto específico (visão detalhada)."""
    df_termo = df[df["produto"] == produto].groupby("termo").agg(
        total_mencoes=("mencoes", "sum"),
        total_positivas=("mencoes_positivas", "sum"),
        total_negativas=("mencoes_negativas", "sum"),
    ).reset_index()
    return df_termo.sort_values(by="total_mencoes", ascending=False)


df_raw = carregar_dados(CAMINHO_PARQUET)

def cor_por_aprovacao(indice):
    if indice < 40:
        return "#ff4757"   # vermelho
    elif indice < 70:
        return "#ffa502"   # laranja
    else:
        return "#2ed573"   # verde

if df_raw.empty:
    st.warning(f"⚠️ Arquivo Parquet não encontrado ou vazio em: `{CAMINHO_PARQUET}`. Certifique-se de rodar o pipeline primeiro.")
else:
    df_produtos = agrupar_por_produto(df_raw)

    # --- SELETOR DE PRODUTO ---
    st.subheader("Selecione um produto para filtrar:")
    opcoes = ["Todos"] + sorted(df_produtos["produto"].unique().tolist())
    produto_selecionado = st.selectbox(
        "Selecione um produto para filtrar:",
        opcoes,
        label_visibility="collapsed",
    )

    st.markdown("---")

    if produto_selecionado == "Todos":
        # --- VISÃO GERAL: cards por produto ---
        registros = df_produtos.to_dict("records")
        colunas_por_linha = 4

        for i in range(0, len(registros), colunas_por_linha):
            cols = st.columns(colunas_por_linha)
            for col, prod in zip(cols, registros[i:i + colunas_por_linha]):
                with col:
                    with st.container(border=True):
                        cor_aprovacao = cor_por_aprovacao(prod['indice_aprovacao'])
                        st.markdown(
                            f"""
                            <div style="padding: 4px 8px 12px 8px;">
                                <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 18px;">
                                    {prod['produto']}
                                </div>
                                <div style="display: flex; flex-direction: row;">
                                    <div>
                                        <div style="font-size: 0.75rem; font-weight: 600; letter-spacing: 1px; color: #888;">
                                            ÍNDICE DE APROVAÇÃO
                                        </div>
                                        <div style="font-size: 3.2rem; font-weight: 800; color: {cor_aprovacao}; line-height: 1;">
                                            {prod['indice_aprovacao']}%
                                        </div>
                                    </div>
                                    <div style="margin-left: 10px">
                                        <div style="font-size: 1rem;">
                                            Menções: {int(prod['total_mencoes'])}
                                        </div>
                                        <div style="font-size: 1rem; color: #2ed573;">
                                            Positivas: {int(prod['total_positivas'])}
                                        </div>
                                        <div style="font-size: 1rem; color: #ff4757;">
                                            Negativas: {int(prod['total_negativas'])}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

        # --- TABELA GERAL (mantida como visão consolidada) ---
        st.subheader("📋 Classificação Geral de Produtos")
        df_exibicao = df_produtos.rename(columns={
            "produto": "Produto",
            "total_mencoes": "Menções Totais",
            "total_videos": "Vídeos Analisados",
            "total_positivas": "Positivas 👍",
            "total_negativas": "Negativas 👎",
            "indice_aprovacao": "Índice de Aprovação (%)",
        })
        st.dataframe(
            df_exibicao,
            column_config={
                "Índice de Aprovação (%)": st.column_config.ProgressColumn(
                    "Índice de Aprovação (%)",
                    help="Porcentagem de menções positivas em relação ao total de sentimentos extraídos",
                    format="%f%%",
                    min_value=0,
                    max_value=100,
                )
            },
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.subheader("📊 Comparativo de Sentimentos entre Produtos")
        df_chart = df_produtos.set_index("produto")[["total_positivas", "total_negativas"]]
        df_chart = df_chart.rename(columns={"total_positivas": "Positivas", "total_negativas": "Negativas"})
        st.bar_chart(df_chart, color=["#2ed573", "#ff4757"])

    else:
        # --- VISÃO DETALHADA: tabela por termo dentro do produto ---
        df_termo = agrupar_por_termo(df_raw, produto_selecionado)

        df_exibicao = df_termo.rename(columns={
            "termo": "Termos",
            "total_mencoes": "Total de Menções",
            "total_positivas": "Positivas",
            "total_negativas": "Negativa",
        })

        st.subheader(f"📋 Detalhamento por termo — {produto_selecionado}")
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)