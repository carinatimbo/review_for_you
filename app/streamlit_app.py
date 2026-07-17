import streamlit as st
import pandas as pd
from pathlib import Path

# Configuração da página do Streamlit
st.set_page_config(page_title="Sentimento do Produto — Gold", layout="wide")

st.title("📊 Painel de Sentimento e Aprovação de Produtos")
st.markdown("Análise consolidada de menções, polaridade de sentimento e índice de aprovação por produto.")

# Caminho para o seu arquivo parquet
CAMINHO_PARQUET = Path("./datalake/gold/reviews/analise_produtos_gold.parquet")

@st.cache_data
def carregar_e_agrupar_por_produto(caminho):
    """Lê o parquet e consolida os dados unicamente por produto."""
    if not caminho.exists():
        return pd.DataFrame()
    
    # 1. Carrega o arquivo Parquet
    df = pd.read_parquet(caminho)
    
    # 2. Agrupa puramente por PRODUTO somando os contadores
    df_produto = df.groupby("produto").agg(
        total_mencoes=("mencoes", "sum"),
        total_videos=("videos", "sum"),
        total_positivas=("mencoes_positivas", "sum"),
        total_negativas=("mencoes_negativas", "sum")
    ).reset_index()
    
    # 3. Recalcula o índice de aprovação consolidado do produto
    # Fórmula segura para evitar divisão por zero se o produto não tiver menções com polaridade
    def calcular_indice(row):
        total_sentimento = row["total_positivas"] + row["total_negativas"]
        if total_sentimento == 0:
            return 0.0
        return round((row["total_positivas"] / total_sentimento) * 100, 1)
        
    df_produto["indice_aprovacao"] = df_produto.apply(calcular_indice, axis=1)
    
    # Ordena pelos produtos com maior aprovação
    return df_produto.sort_values(by="indice_aprovacao", ascending=False)

# Carrega os dados transformados
df_produtos_consolidado = carregar_e_agrupar_por_produto(CAMINHO_PARQUET)

if df_produtos_consolidado.empty:
    st.warning(f"⚠️ Arquivo Parquet não encontrado ou vazio em: `{CAMINHO_PARQUET}`. Certifique-se de rodar o pipeline primeiro.")
else:
    # --- SELETOR DE PRODUTO EM DESTAQUE ---
    st.subheader("🎯 Destaque do Produto")
    produto_foco = st.selectbox("Escolha um produto para detalhar:", df_produtos_consolidado["produto"].unique())
    
    # Filtra a linha do produto selecionado
    dados_foco = df_produtos_consolidado[df_produtos_consolidado["produto"] == produto_foco].iloc[0]
    
    # --- LINHA DE METRICAS (KPIs) 📑 ---
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total de Menções", int(dados_foco["total_mencoes"]))
    col2.metric("Menções Positivas 👍", int(dados_foco["total_positivas"]), delta_color="normal")
    col3.metric("Menções Negativas 👎", int(dados_foco["total_negativas"]), delta=f"-{int(dados_foco['total_negativas'])}" if dados_foco["total_negativas"] > 0 else None, delta_color="inverse")
    
    # Destacando o Índice de Aprovação com formatação de porcentagem
    status_aprovacao = "⭐" if dados_foco["indice_aprovacao"] >= 70 else "⚠️"
    col4.metric(
        label=f"Índice de Aprovação {status_aprovacao}", 
        value=f"{dados_foco['indice_aprovacao']}%",
        delta=f"Equilibrado" if 40 <= dados_foco['indice_aprovacao'] < 70 else ("Bom" if dados_foco['indice_aprovacao'] >= 70 else "Crítico")
    )
    
    st.markdown("---")
    
    # --- VISUALIZAÇÃO GERAL DA CAMADA GOLD ---
    st.subheader("📋 Classificação Geral de Produtos")
    
    # Configurando colunas legíveis para exibição no DataFrame do Streamlit
    df_exibicao = df_produtos_consolidado.rename(columns={
        "produto": "Produto",
        "total_mencoes": "Menções Totais",
        "total_videos": "Vídeos Analisados",
        "total_positivas": "Positivas 👍",
        "total_negativas": "Negativas 👎",
        "indice_aprovacao": "Índice de Aprovação (%)"
    })
    
    # Renderizando a tabela interativa com uma barra visual direto na coluna de aprovação
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
        hide_index=True
    )
    
    # --- GRÁFICO COMPARATIVO COMPLEMENTAR ---
    st.markdown("---")
    st.subheader("📊 Comparativo de Sentimentos entre Produtos")
    
    # Prepara o DataFrame para um gráfico de barras empilhadas ou lado a lado
    df_chart = df_produtos_consolidado.set_index("produto")[["total_positivas", "total_negativas"]]
    df_chart = df_chart.rename(columns={"total_positivas": "Positivas", "total_negativas": "Negativas"})
    
    st.bar_chart(df_chart, color=["#2ed573", "#ff4757"]) # Cores customizadas: Verde para Positivo, Vermelho para Negativo