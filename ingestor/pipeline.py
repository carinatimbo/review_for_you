# -*- coding: utf-8 -*-
"""
Pipeline de ingestao perene — orquestra um ciclo completo para UM canal.

Fluxo de um ciclo:
  descobrir (incremental via watermark)
    -> para cada video novo e nao-ingerido (idempotencia):
         captar transcricao  (BRONZE)
         limpar + contrato    (SILVER)
       persiste parquet + atualiza estado SQLite
    -> roda analitico do dominio (GOLD)
    -> avanca o watermark do canal

Tudo escrito de forma que rodar o mesmo ciclo duas vezes NAO duplica dados.
"""
from __future__ import annotations
import re
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import duckdb
import pandera.pandas as pa
from pandera.pandas import Column, DataFrameSchema, Check

from .state import StateStore, content_hash
from .discovery import get_discovery
from .transcript import extrair_transcricao
from .transcript import identificar_produto_por_palavra_chave

log = logging.getLogger("ingestor")

STOPWORDS = {"entao", "olha", "ne", "tipo", "veja", "bem", "o", "a", "que",
             "de", "e", "aqui", "isso", "na", "pratica"}

# Mesmo contrato Silver dos 10 notebooks (Desafio 1), incluindo n_palavras.
SILVER_SCHEMA = DataFrameSchema({
    "video_id":     Column(str, nullable=False),
    "ordem":        Column(int, Check.ge(0)),
    "texto_limpo":  Column(str, Check.str_length(min_value=1)),
    "start":        Column(float, Check.ge(0)),
    "duration":     Column(float, Check.gt(0)),
    "n_palavras":   Column(int, Check.ge(1)),
    "produto":      Column(str, nullable=False),
    "titulo_video": Column(str, nullable=False), # 🌟 ADICIONE ESTA LINHA
}, coerce=True)


def _limpar(texto: str) -> str:
    texto = re.sub(r"[^a-zaaaeeiooouuc\s]", " ", texto.lower())
    return " ".join(t for t in texto.split()
                    if t not in STOPWORDS and len(t) > 2)


def _bronze_silver(video_id, trechos, produto: str, titulo_video: str) -> pd.DataFrame:
    df = pd.DataFrame([
        {"video_id": video_id, "ordem": i, "texto": t["text"],
         "start": float(t["start"]), "duration": float(t["duration"])}
        for i, t in enumerate(trechos)
    ])
    df["texto_limpo"] = df["texto"].apply(_limpar)
    df = df[df["texto_limpo"].str.len() > 0].copy()
    df["n_palavras"] = df["texto_limpo"].str.split().str.len().fillna(0).astype(int)
    df["produto"] = produto
    df["titulo_video"] = titulo_video
    return SILVER_SCHEMA.validate(df[["video_id", "ordem", "texto_limpo",
                                      "start", "duration", "n_palavras",
                                      "produto", "titulo_video"]])


def _persistir(df: pd.DataFrame, dominio: str, video_id: str, produto: str):
    dia = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    produto_pasta = produto.lower().replace(" ", "_").replace("/", "-")
    base = Path(f"./datalake/silver/{dominio}/{produto_pasta}/{dia}")
    base.mkdir(parents=True, exist_ok=True)
    df.to_parquet(base / f"{video_id}.parquet", index=False)


def _gold(dominio: str, vocabulario: list[str]):
    """Consolida o analítico na camada GOLD separando por produto."""
    # O asterisco triplo (***) garante que o DuckDB leia todas as subpastas de produtos
    src = f"./datalake/silver/{dominio}/**/*.parquet"
    con = duckdb.connect()
    termos = "', '".join(vocabulario) if vocabulario else "x"
    
    try:
        # A query agora agrupa por PRODUTO e por TERMO (opinião/palavra-chave)
        gold = con.execute(f"""
            WITH s AS (SELECT * FROM read_parquet('{src}')),
                 alvo AS (SELECT UNNEST(['{termos}']) AS termo)
            SELECT 
                s.produto,
                s.titulo_video, -- 🌟 Agora você pode puxar o título aqui
                a.termo, 
                COUNT(*) AS mencoes,
                COUNT(DISTINCT s.video_id) AS videos
            FROM s 
            JOIN alvo a ON s.texto_limpo LIKE '%' || a.termo || '%'
            GROUP BY s.produto, s.titulo_video, a.termo 
            ORDER BY s.produto, mencoes DESC
        """).df()
        
        out = Path(f"./datalake/gold/{dominio}")
        out.mkdir(parents=True, exist_ok=True)
        
        # Salva o resultado final consolidado por produto
        gold.to_parquet(out / "analise_produtos_gold.parquet", index=False)
        return gold
    except duckdb.IOException:
        return pd.DataFrame()   # ainda sem dados silver
    finally:
        con.close()


def rodar_ciclo(canal: dict, glob_cfg: dict, store: StateStore) -> dict:
    """Executa um ciclo completo de ingestao para um canal. Idempotente."""
    cid, dom = canal["channel_id"], canal["dominio"]
    vocab = canal.get("vocabulario", [])
    disc = get_discovery(glob_cfg.get("modo_demo", True))

    watermark = store.get_watermark(cid)
    videos = disc.descobrir(cid, watermark,
                            canal.get("max_videos_por_ciclo", 5),
                            glob_cfg.get("janela_descoberta_dias", 30))

    novos, ingeridos, pulados, falhas, max_pub = 0, 0, 0, 0, watermark or ""
    for v in videos:
        store.marcar_descoberto(v.video_id, cid, dom, v.published_at, v.title)
        max_pub = max(max_pub, v.published_at or "")
        novos += 1

        trechos = extrair_transcricao(
            v.video_id, glob_cfg.get("idiomas_legenda", ["pt", "en"]),
            vocab, glob_cfg.get("modo_demo", True))
        if not trechos:
            store.marcar_falha(v.video_id, "sem legenda")
            falhas += 1
            continue

        texto_total = " ".join(t["text"] for t in trechos)
        h = content_hash(texto_total)
        if store.ja_ingerido(v.video_id, h):   # IDEMPOTENCIA
            pulados += 1
            continue
        try:
            produto_detectado = identificar_produto_por_palavra_chave(texto_total)
            df = _bronze_silver(v.video_id, trechos, produto_detectado, v.title)
            _persistir(df, dom, v.video_id, produto_detectado)
            store.marcar_ingerido(v.video_id, h, len(df))
            ingeridos += 1
        except (pa.errors.SchemaError, Exception) as e:
            store.marcar_falha(v.video_id, e)
            falhas += 1

    if novos:
        store.update_watermark(cid, max_pub, ingeridos)
    _gold(dom, vocab)

    res = {"canal": canal["nome"], "descobertos": novos, "ingeridos": ingeridos,
           "pulados_idempotencia": pulados, "falhas": falhas}
    log.info("ciclo %s -> %s", canal["nome"], res)
    return res
