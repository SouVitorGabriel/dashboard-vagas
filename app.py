from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import streamlit as st

from src.features import build_features, hard_signal_overview, tech_frequency
from src.github_issues import GitHubFetchError, fetch_issues
from src.ml_pipeline import analyze_trend, build_time_series, cluster_texts, difficulty_terms

st.set_page_config(page_title="PI4 - Vagas Junior", layout="wide")

st.title("Prototipo: Vagas Junior BR (GitHub Issues)")
st.caption(
    "Fluxo inicial para relatorio parcial: captura automatica de issues, extracao de sinais de exigencia e blocos de visualizacao."
)

st.sidebar.header("Parametros")
owner = st.sidebar.text_input("Owner", value="backend-br")
repo = st.sidebar.text_input("Repositorio", value="vagas")
state = st.sidebar.selectbox("Estado das issues", options=["all", "open", "closed"], index=0)
limit = st.sidebar.slider("Quantidade de issues", min_value=30, max_value=200, value=100, step=10)
only_junior = st.sidebar.checkbox("Filtrar somente junior/trainee/estagio", value=True)
only_portuguese = st.sidebar.checkbox("Filtrar somente textos em portugues", value=True)

refresh = st.sidebar.button("Atualizar coleta")
if refresh:
    st.cache_data.clear()


def _resolve_token() -> str | None:
    secret_token = None
    try:
        secret_token = st.secrets.get("GITHUB_TOKEN")
    except Exception:
        secret_token = None

    return secret_token or os.getenv("GITHUB_TOKEN")


@st.cache_data(ttl=3600)
def load_dataset(
    owner_value: str,
    repo_value: str,
    state_value: str,
    limit_value: int,
    token_value: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    issues = fetch_issues(
        owner=owner_value,
        repo=repo_value,
        limit=limit_value,
        state=state_value,
        token=token_value,
    )

    raw_df = pd.DataFrame(issues)
    if raw_df.empty:
        return raw_df, raw_df

    features_df = build_features(raw_df)
    return raw_df, features_df


token = _resolve_token()
if token:
    st.sidebar.success("Token GitHub detectado")
else:
    st.sidebar.warning("Sem token. Limite de API menor (60 requests/hora).")

try:
    raw, featured = load_dataset(owner, repo, state, limit, token)
except GitHubFetchError as exc:
    st.error(f"Falha na coleta: {exc}")
    st.stop()

if raw.empty:
    st.warning("Nenhuma issue encontrada para os parametros informados.")
    st.stop()

analysis = featured.copy()
if only_junior:
    analysis = analysis[analysis["is_junior"]]
if only_portuguese:
    analysis = analysis[analysis["is_portuguese"]]

analysis = analysis[analysis["text_norm"].str.len() > 30]

if analysis.empty:
    st.warning(
        "Nao sobraram vagas apos os filtros. Desmarque algum filtro para visualizar dados e validar o pipeline."
    )
    st.dataframe(featured[["issue_number", "title", "created_at", "is_junior", "is_portuguese"]].head(20))
    st.stop()

series = build_time_series(analysis)
trend = analyze_trend(series)

junior_rate = featured["is_junior"].mean() * 100.0
pt_rate = featured["is_portuguese"].mean() * 100.0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Issues capturadas", f"{len(raw)}")
c2.metric("Taxa de vagas junior", f"{junior_rate:.1f}%")
c3.metric("Taxa de portugues", f"{pt_rate:.1f}%")
c4.metric("Amostra analisada", f"{len(analysis)}")
c5.metric("Exigencia media", f"{analysis['difficulty_score'].mean():.2f}")

c6, c7, c8 = st.columns(3)
c6.metric("Tendencia da exigencia", trend["direction"])
c7.metric("Inclinacao por periodo", f"{trend['slope']:.3f}")
c8.metric("Variacao inicial-final", f"{trend['delta_pct']:.1f}%")

st.subheader("Evolucao temporal")
if series.empty:
    st.info("Sem dados suficientes para serie temporal.")
else:
    fig_trend = px.line(
        series,
        x="period",
        y="avg_difficulty",
        markers=True,
        title="Exigencia media por periodo",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    fig_count = px.bar(series, x="period", y="n_jobs", title="Quantidade de vagas por periodo")
    st.plotly_chart(fig_count, use_container_width=True)

st.subheader("Sinais de cobranca")
col_a, col_b = st.columns(2)

with col_a:
    fig_dist = px.histogram(
        analysis,
        x="difficulty_score",
        color="difficulty_class",
        nbins=10,
        title="Distribuicao do indice de exigencia",
    )
    st.plotly_chart(fig_dist, use_container_width=True)

with col_b:
    signal_df = hard_signal_overview(analysis)
    signal_df["percent"] = signal_df["rate"] * 100.0
    fig_signals = px.bar(
        signal_df,
        x="signal",
        y="percent",
        title="Percentual de vagas com sinais de cobranca",
    )
    fig_signals.update_layout(xaxis_title="", yaxis_title="%")
    st.plotly_chart(fig_signals, use_container_width=True)

st.subheader("Tecnologias mais citadas")
tech_df = tech_frequency(analysis).head(12)
if tech_df.empty:
    st.info("Sem dados de tecnologia suficientes.")
else:
    fig_tech = px.bar(tech_df, x="tech", y="count", title="Top tecnologias citadas")
    st.plotly_chart(fig_tech, use_container_width=True)

st.subheader("ML - Agrupamento de vagas por similaridade de texto")
cluster_payload = cluster_texts(analysis, n_clusters=3)
if cluster_payload is None:
    st.info("Amostra pequena para clustering. Aumente o limite de issues.")
else:
    cluster_df, top_terms_df = cluster_payload
    fig_cluster = px.scatter(
        cluster_df,
        x="x",
        y="y",
        color="cluster",
        hover_data=["issue_number", "title", "difficulty_score"],
        title="Clusters de texto (SVD 2D)",
    )
    st.plotly_chart(fig_cluster, use_container_width=True)
    st.dataframe(top_terms_df, use_container_width=True)

st.subheader("ML - Termos associados a maior exigencia")
terms_df = difficulty_terms(analysis)
if terms_df is None:
    st.info("Sem volume suficiente para estimar termos discriminantes.")
else:
    st.dataframe(terms_df, use_container_width=True)

st.subheader("Tabela de amostra para o relatorio")
preview_cols = [
    "issue_number",
    "title",
    "created_at",
    "difficulty_score",
    "difficulty_class",
    "years_required",
    "tech_count",
    "requires_english",
    "has_advanced_stack",
    "has_hard_process",
]
st.dataframe(analysis[preview_cols].sort_values("created_at", ascending=False).head(50), use_container_width=True)

csv_bytes = analysis.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Baixar CSV da amostra analisada",
    data=csv_bytes,
    file_name=f"{owner}_{repo}_sample_features.csv",
    mime="text/csv",
)
