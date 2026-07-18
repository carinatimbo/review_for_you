import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(page_title="Review For You", layout="wide", page_icon="▶️")

CAMINHO_PARQUET = Path("./datalake/gold/reviews/analise_produtos_gold.parquet")

# =============================================================================
# TOKENS DE DESIGN
# =============================================================================
COR_BG = "#0B0E14"
COR_PAINEL = "#131722"
COR_BORDA = "rgba(255,255,255,0.08)"
COR_TEXTO = "#E8EAED"
COR_TEXTO_MUTED = "#7B8494"
COR_ACCENT = "#35D0C0"          # ciano-sinal — cor de marca / UI, nunca de dado
COR_VERDE = "#3ECF8E"           # aprovação 70–100
COR_LARANJA = "#F5A623"         # aprovação 40–69
COR_VERMELHO = "#F0525D"        # aprovação 0–39


def cor_por_aprovacao(indice: float) -> str:
    if indice < 40:
        return COR_VERMELHO
    elif indice < 70:
        return COR_LARANJA
    return COR_VERDE


def barra_sinal(indice: float, cor: str, segmentos: int = 24) -> str:
    """Renderiza o índice de aprovação como uma barra de sinal segmentada
    (estilo VU-meter), reforçando a métrica como 'força de sinal' captada."""
    preenchidos = round((indice / 100) * segmentos)
    ticks = []
    for i in range(segmentos):
        ativo = i < preenchidos
        cor_tick = cor if ativo else "rgba(255,255,255,0.09)"
        altura = 10 + int((i / segmentos) * 14)  # ticks crescem da esquerda p/ direita
        ticks.append(
            f'<span style="display:inline-block;width:5px;height:{altura}px;'
            f'margin-right:3px;background:{cor_tick};border-radius:1px;"></span>'
        )
    return f'<div style="display:flex;align-items:flex-end;">{"".join(ticks)}</div>'


# =============================================================================
# CSS GLOBAL
# =============================================================================
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background-color: {COR_BG};
        background-image:
            repeating-linear-gradient(0deg, rgba(255,255,255,0.012) 0px, rgba(255,255,255,0.012) 1px, transparent 1px, transparent 3px);
    }}

    /* ---------- Barra de identificação (header estilo broadcast) ---------- */
    .ident-bar {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 4px;
    }}
    .ident-tally {{
        width: 9px; height: 9px; border-radius: 50%;
        background: {COR_ACCENT};
        box-shadow: 0 0 8px {COR_ACCENT};
        flex-shrink: 0;
    }}
    .ident-label {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 2px;
        color: {COR_ACCENT};
        text-transform: uppercase;
    }}
    .titulo-principal {{
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 2.1rem;
        color: {COR_TEXTO};
        margin: 6px 0 2px 0;
    }}
    .subtitulo {{
        font-family: 'Inter', sans-serif;
        font-size: 0.92rem;
        color: {COR_TEXTO_MUTED};
        margin-bottom: 20px;
    }}

    /* ---------- Rótulo de seção estilo telemetria ---------- */
    .secao-label {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 2px;
        color: {COR_TEXTO_MUTED};
        text-transform: uppercase;
        border-bottom: 1px solid {COR_BORDA};
        padding-bottom: 8px;
        margin: 28px 0 16px 0;
    }}

    /* ---------- Cards de produto ---------- */
    .signal-card {{
        background: {COR_PAINEL};
        border: 1px solid {COR_BORDA};
        border-radius: 6px;
        padding: 18px 20px 20px 20px;
        margin-bottom: 16px;
        position: relative;
        overflow: hidden;
    }}
    .signal-card::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: var(--faixa-cor);
    }}
    .signal-card-titulo {{
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.12rem;
        color: {COR_TEXTO};
        margin-bottom: 16px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .signal-card-pct {{
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        font-size: 2.6rem;
        line-height: 1;
        margin-bottom: 6px;
    }}
    .signal-card-eyebrow {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 1.5px;
        color: {COR_TEXTO_MUTED};
        text-transform: uppercase;
    }}
    .signal-card-stats {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.84rem;
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-top: 16px;
        border-top: 1px solid {COR_BORDA};
        padding-top: 12px;
    }}
    .stat-row {{ display: flex; justify-content: space-between; }}
    .stat-label {{ color: {COR_TEXTO_MUTED}; }}

    /* ---------- Tabela de detalhamento por termo ---------- */
    .termo-header {{
        display: flex;
        align-items: baseline;
        gap: 14px;
        margin-bottom: 4px;
    }}
    .termo-produto-nome {{
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.6rem;
        color: {COR_TEXTO};
    }}

    /* Ajustes leves em componentes nativos do Streamlit */
    div[data-testid="stSelectbox"] label {{
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 0.72rem !important;
        letter-spacing: 1.5px;
        color: {COR_TEXTO_MUTED} !important;
        text-transform: uppercase;
    }}
    div[data-baseweb="select"] > div {{
        background-color: {COR_PAINEL} !important;
        border-color: {COR_BORDA} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# CARREGAMENTO E TRANSFORMAÇÃO DE DADOS
# =============================================================================

@st.cache_data
def carregar_dados(caminho):
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
    df_termo = df[df["produto"] == produto].groupby("termo").agg(
        total_mencoes=("mencoes", "sum"),
        total_positivas=("mencoes_positivas", "sum"),
        total_negativas=("mencoes_negativas", "sum"),
    ).reset_index()
    df_termo["indice_aprovacao"] = df_termo.apply(
        lambda row: calcular_indice(row["total_positivas"], row["total_negativas"]), axis=1
    )
    return df_termo.sort_values(by="total_mencoes", ascending=False)


df_raw = carregar_dados(CAMINHO_PARQUET)

# =============================================================================
# CABEÇALHO
# =============================================================================
st.markdown(
    f"""
    <div class="ident-bar">
        <div class="ident-tally"></div>
        <div class="ident-label">Review For You · Telemetria · {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
    </div>
    <div class="titulo-principal">Painel de Sentimento de Produtos</div>
    <div class="subtitulo">Sinal de aprovação extraído de menções em vídeos de review — atualizado a cada ciclo de ingestão.</div>
    """,
    unsafe_allow_html=True,
)

if df_raw.empty:
    st.warning(f"⚠️ Arquivo Parquet não encontrado ou vazio em: `{CAMINHO_PARQUET}`. Certifique-se de rodar o pipeline primeiro.")
    st.stop()

df_produtos = agrupar_por_produto(df_raw)

# =============================================================================
# SELETOR
# =============================================================================
opcoes = ["Todos"] + sorted(df_produtos["produto"].unique().tolist())
produto_selecionado = st.selectbox("Selecione um produto para filtrar", opcoes)

# =============================================================================
# VISÃO GERAL — "TODOS"
# =============================================================================
if produto_selecionado == "Todos":
    st.markdown('<div class="secao-label">Sinal por produto</div>', unsafe_allow_html=True)

    registros = df_produtos.to_dict("records")
    colunas_por_linha = 4

    for i in range(0, len(registros), colunas_por_linha):
        cols = st.columns(colunas_por_linha)
        for col, prod in zip(cols, registros[i:i + colunas_por_linha]):
            with col:
                cor = cor_por_aprovacao(prod["indice_aprovacao"])
                st.markdown(
                    f"""
                    <div class="signal-card" style="--faixa-cor: {cor};">
                        <div class="signal-card-titulo">{prod['produto']}</div>
                        <div class="signal-card-eyebrow">Índice de aprovação</div>
                        <div class="signal-card-pct" style="color:{cor};">{prod['indice_aprovacao']}%</div>
                        {barra_sinal(prod['indice_aprovacao'], cor)}
                        <div class="signal-card-stats">
                            <div class="stat-row"><span class="stat-label">Menções</span><span>{int(prod['total_mencoes'])}</span></div>
                            <div class="stat-row"><span class="stat-label">Positivas</span><span style="color:{COR_VERDE};">{int(prod['total_positivas'])}</span></div>
                            <div class="stat-row"><span class="stat-label">Negativas</span><span style="color:{COR_VERMELHO};">{int(prod['total_negativas'])}</span></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown('<div class="secao-label">Classificação geral</div>', unsafe_allow_html=True)
    df_exibicao = df_produtos.rename(columns={
        "produto": "Produto",
        "total_mencoes": "Menções Totais",
        "total_videos": "Vídeos Analisados",
        "total_positivas": "Positivas",
        "total_negativas": "Negativas",
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

    st.markdown('<div class="secao-label">Comparativo de sentimentos</div>', unsafe_allow_html=True)
    df_chart = df_produtos.set_index("produto")[["total_positivas", "total_negativas"]]
    df_chart = df_chart.rename(columns={"total_positivas": "Positivas", "total_negativas": "Negativas"})
    st.bar_chart(df_chart, color=[COR_VERDE, COR_VERMELHO])

# =============================================================================
# VISÃO DETALHADA — PRODUTO ESPECÍFICO
# =============================================================================
else:
    dados_foco = df_produtos[df_produtos["produto"] == produto_selecionado].iloc[0]
    cor_foco = cor_por_aprovacao(dados_foco["indice_aprovacao"])

    st.markdown(
        f"""
        <div class="signal-card" style="--faixa-cor: {cor_foco}; margin-top: 8px;">
            <div class="termo-header">
                <span class="termo-produto-nome">{produto_selecionado}</span>
            </div>
            <div class="signal-card-pct" style="color:{cor_foco}; margin-top: 14px;">{dados_foco['indice_aprovacao']}%</div>
            <div class="signal-card-eyebrow">Índice de aprovação geral</div>
            {barra_sinal(dados_foco['indice_aprovacao'], cor_foco, segmentos=40)}
            <div class="signal-card-stats" style="flex-direction: row; justify-content: flex-start; gap: 40px;">
                <div class="stat-row" style="gap:8px;"><span class="stat-label">Menções</span><span>{int(dados_foco['total_mencoes'])}</span></div>
                <div class="stat-row" style="gap:8px;"><span class="stat-label">Positivas</span><span style="color:{COR_VERDE};">{int(dados_foco['total_positivas'])}</span></div>
                <div class="stat-row" style="gap:8px;"><span class="stat-label">Negativas</span><span style="color:{COR_VERMELHO};">{int(dados_foco['total_negativas'])}</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="secao-label">Detalhamento por termo</div>', unsafe_allow_html=True)

    df_termo = agrupar_por_termo(df_raw, produto_selecionado)
    df_exibicao = df_termo.rename(columns={
        "termo": "Termo",
        "total_mencoes": "Total de Menções",
        "total_positivas": "Positivas",
        "total_negativas": "Negativas",
        "indice_aprovacao": "Índice de Aprovação (%)",
    })
    st.dataframe(
        df_exibicao,
        column_config={
            "Índice de Aprovação (%)": st.column_config.ProgressColumn(
                "Índice de Aprovação (%)",
                format="%f%%",
                min_value=0,
                max_value=100,
            )
        },
        use_container_width=True,
        hide_index=True,
    )