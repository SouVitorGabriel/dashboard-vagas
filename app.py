from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import streamlit as st

from src.features import build_features, hard_signal_overview, tech_frequency
from src.github_issues import GitHubFetchError, fetch_issues
from src.ml_pipeline import (
    MIN_CLUSTER_SAMPLE,
    MIN_TERMS_SAMPLE,
    analyze_trend,
    build_time_series,
    cluster_texts,
    difficulty_terms,
)

st.set_page_config(page_title="PI4 - Vagas Junior", layout="wide")

st.title("Prototipo: Vagas Junior BR (GitHub Issues)")
st.caption(
    "Fluxo inicial para relatorio parcial: captura automatica de issues, extracao de sinais de exigencia e blocos de visualizacao."
)

st.sidebar.header("Parametros")
owner = st.sidebar.text_input("Owner", value="backend-br")
repo = st.sidebar.text_input("Repositorio", value="vagas")
state = st.sidebar.selectbox("Estado das issues", options=["all", "open", "closed"], index=0)
limit = st.sidebar.slider("Quantidade de issues", min_value=30, max_value=1000, value=200, step=10)
only_junior = st.sidebar.checkbox("Filtrar somente junior/trainee/estagio", value=True)
only_portuguese = st.sidebar.checkbox("Filtrar somente textos em portugues", value=True)
cluster_count = st.sidebar.slider("Quantidade de clusters (ML)", min_value=2, max_value=6, value=3)
st.sidebar.caption("Dica: para blocos de ML mais estaveis, use 300+ issues quando possivel.")

refresh = st.sidebar.button("Atualizar coleta")
if refresh:
    st.cache_data.clear()


def render_loading_placeholders() -> None:
    st.subheader("Carregando dashboard")
    st.caption(
        "A aplicacao esta coletando issues no GitHub e processando os sinais iniciais. "
        "Isso pode levar alguns segundos."
    )

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Issues capturadas", "...")
    m2.metric("Taxa de vagas junior", "...")
    m3.metric("Taxa de portugues", "...")
    m4.metric("Amostra analisada", "...")
    m5.metric("Exigencia media", "...")

    p1, p2 = st.columns(2)
    with p1:
        st.info("Preparando graficos de evolucao temporal...")
        st.info("Preparando distribuicao do indice de exigencia...")
    with p2:
        st.info("Preparando sinais de cobranca e tabelas...")
        st.info("Preparando blocos de ML...")


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

loading_placeholder = st.empty()
status_placeholder = st.empty()

with loading_placeholder.container():
    render_loading_placeholders()

try:
    with status_placeholder.container():
        with st.status("Carregando dados para analise...", expanded=True) as status:
            status.write("1/3 - Conectando na API do GitHub")
            status.write("2/3 - Baixando issues e removendo pull requests")
            status.write("3/3 - Processando features e preparando amostra")
            raw, featured = load_dataset(owner, repo, state, limit, token)
            status.update(label="Dados carregados. Montando visualizacoes...", state="running")
except GitHubFetchError as exc:
    loading_placeholder.empty()
    status_placeholder.empty()
    st.error(f"Falha na coleta: {exc}")
    st.stop()

if raw.empty:
    loading_placeholder.empty()
    status_placeholder.empty()
    st.warning("Nenhuma issue encontrada para os parametros informados.")
    st.stop()

analysis = featured.copy()
funnel_rows: list[dict[str, float | str]] = []
base_count = len(analysis)
funnel_rows.append({"etapa": "Issues capturadas (sem PR)", "quantidade": base_count})

if only_junior:
    analysis = analysis[analysis["is_junior"]]
    funnel_rows.append({"etapa": "Apos filtro junior/trainee/estagio", "quantidade": len(analysis)})
else:
    funnel_rows.append({"etapa": "Sem filtro de senioridade", "quantidade": len(analysis)})

if only_portuguese:
    analysis = analysis[analysis["is_portuguese"]]
    funnel_rows.append({"etapa": "Apos filtro de portugues", "quantidade": len(analysis)})
else:
    funnel_rows.append({"etapa": "Sem filtro de idioma", "quantidade": len(analysis)})

analysis = analysis[analysis["text_norm"].str.len() > 30]
funnel_rows.append({"etapa": "Texto minimo (> 30 caracteres)", "quantidade": len(analysis)})

funnel_df = pd.DataFrame(funnel_rows)
funnel_df["retencao_percentual"] = (
    (funnel_df["quantidade"] / max(1, base_count)) * 100.0
).round(1)
funnel_df["perda_acumulada"] = base_count - funnel_df["quantidade"]

if analysis.empty:
    loading_placeholder.empty()
    status_placeholder.empty()
    st.warning(
        "Nao sobraram vagas apos os filtros. Desmarque algum filtro para visualizar dados e validar o pipeline."
    )
    st.subheader("Funil da amostra")
    st.dataframe(funnel_df, use_container_width=True)
    empty_view = featured[["issue_number", "title", "created_at", "is_junior", "is_portuguese"]].rename(
        columns={
            "issue_number": "numero_issue",
            "title": "titulo",
            "created_at": "criado_em",
            "is_junior": "eh_junior",
            "is_portuguese": "eh_portugues",
        }
    )
    st.dataframe(empty_view.head(20), use_container_width=True)
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

st.subheader("Funil da amostra (por que 200 podem virar 18)")
st.caption(
    "A amostra final considera os filtros ativos (junior e portugues) e remove textos muito curtos. "
    "Por isso o total analisado pode cair bastante."
)

fcol1, fcol2 = st.columns([1, 2])
with fcol1:
    st.dataframe(funnel_df, use_container_width=True)
with fcol2:
    fig_funnel = px.bar(
        funnel_df,
        x="etapa",
        y="quantidade",
        text="quantidade",
        title="Contagem por etapa do funil",
    )
    fig_funnel.update_layout(xaxis_title="", yaxis_title="vagas")
    st.plotly_chart(fig_funnel, use_container_width=True)

st.subheader("Evolucao temporal")
if series.empty:
    st.info(
        "Sem dados suficientes para serie temporal apos remover o mes corrente (incompleto)."
    )
else:
    st.caption("O mes corrente e removido automaticamente para evitar distorcao por periodo incompleto.")
    fig_trend = px.line(
        series,
        x="periodo",
        y="exigencia_media",
        markers=True,
        title="Exigencia media por periodo (meses completos)",
    )
    fig_trend.update_layout(xaxis_title="Periodo", yaxis_title="Indice medio de exigencia")
    st.plotly_chart(fig_trend, use_container_width=True)

    fig_count = px.bar(
        series,
        x="periodo",
        y="quantidade_vagas",
        title="Quantidade de vagas por periodo",
    )
    fig_count.update_layout(xaxis_title="Periodo", yaxis_title="Quantidade de vagas")
    st.plotly_chart(fig_count, use_container_width=True)

st.subheader("Sinais de cobranca")
distribution_mode = st.radio(
    "Como exibir a distribuicao do indice de exigencia:",
    options=["Faixas de score", "Classes baixo/medio/alto"],
    horizontal=True,
)

col_a, col_b = st.columns(2)

with col_a:
    if distribution_mode == "Faixas de score":
        max_score = max(6.0, float(analysis["difficulty_score"].max()))
        upper_edge = int(max_score) + 2
        bins = list(range(0, upper_edge))
        binned = pd.cut(analysis["difficulty_score"], bins=bins, right=False, include_lowest=True)
        dist_df = binned.value_counts(sort=False).reset_index()
        dist_df.columns = ["faixa_score", "vagas"]
        dist_df["faixa_score"] = dist_df["faixa_score"].astype(str)

        fig_dist = px.bar(
            dist_df,
            x="faixa_score",
            y="vagas",
            title="Distribuicao do indice por faixas de score",
        )
        fig_dist.update_layout(xaxis_title="Faixa do score", yaxis_title="Quantidade de vagas")
        st.plotly_chart(fig_dist, use_container_width=True)
        st.caption("Cada barra representa quantas vagas cairam no intervalo de score mostrado no eixo X.")
    else:
        class_order = ["baixo", "medio", "alto"]
        class_df = (
            analysis["difficulty_class"]
            .value_counts()
            .reindex(class_order, fill_value=0)
            .reset_index()
        )
        class_df.columns = ["classe", "vagas"]
        fig_dist = px.bar(
            class_df,
            x="classe",
            y="vagas",
            title="Distribuicao por classe de exigencia",
        )
        fig_dist.update_layout(xaxis_title="Classe", yaxis_title="Quantidade de vagas")
        st.plotly_chart(fig_dist, use_container_width=True)
        st.caption("As classes seguem o score: baixo (0-2), medio (2.1-4.0), alto (>4.0).")

with col_b:
    signal_df = hard_signal_overview(analysis)
    signal_df["percentual"] = (signal_df["taxa"] * 100.0).round(1)
    show_zero_signals = st.checkbox("Mostrar sinais com valor zero", value=False)

    if show_zero_signals:
        signal_plot_df = signal_df.copy()
    else:
        signal_plot_df = signal_df[signal_df["quantidade"] > 0].copy()

    if signal_plot_df.empty:
        st.info("Nenhum sinal com ocorrencia na amostra atual.")
    else:
        fig_signals = px.bar(
            signal_plot_df,
            x="sinal",
            y="percentual",
            text="quantidade",
            title="Percentual de vagas com sinais de cobranca",
        )
        fig_signals.update_layout(xaxis_title="", yaxis_title="% das vagas")
        st.plotly_chart(fig_signals, use_container_width=True)

    st.caption("Definicoes dos sinais utilizados:")
    st.dataframe(
        signal_df[["sinal", "definicao", "quantidade", "percentual"]],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Detalhamento: mismatch junior/pleno-senior")
mismatch_df = analysis[analysis["senior_mismatch"]].copy()
if mismatch_df.empty:
    st.info("Nenhum caso de mismatch foi encontrado com os filtros atuais.")
else:
    for list_col in ["senior_terms_found", "advanced_terms_found", "process_terms_found"]:
        mismatch_df[list_col] = mismatch_df[list_col].map(
            lambda values: ", ".join(values) if isinstance(values, list) else ""
        )

    mismatch_df = mismatch_df.rename(
        columns={
            "issue_number": "numero_issue",
            "title": "titulo",
            "created_at": "criado_em",
            "years_required": "anos_experiencia_exigidos",
            "tech_count": "quantidade_tecnologias",
            "requires_english": "exige_ingles",
            "senior_terms_found": "termos_pleno_senior",
            "advanced_terms_found": "termos_stack_avancada",
            "process_terms_found": "termos_processo_exigente",
        }
    )

    st.caption(
        "Mismatch significa: vaga classificada como junior, mas com termos tipicos de pleno/senior no texto."
    )
    mismatch_cols = [
        "numero_issue",
        "titulo",
        "criado_em",
        "anos_experiencia_exigidos",
        "quantidade_tecnologias",
        "exige_ingles",
        "termos_pleno_senior",
        "termos_stack_avancada",
        "termos_processo_exigente",
    ]
    st.dataframe(
        mismatch_df[mismatch_cols].sort_values("criado_em", ascending=False).head(50),
        use_container_width=True,
    )

st.subheader("Tecnologias mais citadas")
tech_df = tech_frequency(analysis).head(12)
if tech_df.empty:
    st.info("Sem dados de tecnologia suficientes.")
else:
    fig_tech = px.bar(tech_df, x="tech", y="count", title="Top tecnologias citadas")
    st.plotly_chart(fig_tech, use_container_width=True)

st.subheader("ML - Agrupamento de vagas por similaridade de texto")
if len(analysis) < MIN_CLUSTER_SAMPLE:
    missing = MIN_CLUSTER_SAMPLE - len(analysis)
    st.info(
        f"Volume insuficiente para clustering estavel. Minimo recomendado: {MIN_CLUSTER_SAMPLE}. "
        f"Atual: {len(analysis)}. Faltam: {missing}."
    )
else:
    cluster_payload = cluster_texts(analysis, n_clusters=cluster_count)
    if cluster_payload is None:
        st.info("Nao foi possivel gerar clusters com qualidade. Tente aumentar a amostra.")
    else:
        cluster_df, top_terms_df = cluster_payload
        fig_cluster = px.scatter(
            cluster_df,
            x="componente_1",
            y="componente_2",
            color="grupo",
            hover_data=["numero_issue", "titulo", "indice_exigencia"],
            title="Clusters de texto (SVD 2D)",
        )
        fig_cluster.update_layout(
            xaxis_title="Componente 1",
            yaxis_title="Componente 2",
            legend_title="Grupo",
        )
        st.plotly_chart(fig_cluster, use_container_width=True)
        st.caption(
            "Top termos por cluster apos limpeza de URLs/ruido e stopwords comuns de anuncios de vaga."
        )
        st.dataframe(top_terms_df, use_container_width=True)

st.subheader("ML - Termos associados a maior exigencia")
if len(analysis) < MIN_TERMS_SAMPLE:
    missing = MIN_TERMS_SAMPLE - len(analysis)
    st.info(
        f"Sem volume suficiente para termos discriminantes. Minimo: {MIN_TERMS_SAMPLE}. "
        f"Atual: {len(analysis)}. Faltam: {missing}."
    )
else:
    terms_df = difficulty_terms(analysis)
    if terms_df is None:
        st.info(
            "Nao foi possivel estimar termos discriminantes com estabilidade estatistica na amostra atual."
        )
    else:
        st.dataframe(terms_df, use_container_width=True)

st.subheader("Tabela de amostra para o relatorio")
preview_df = analysis.copy()
for list_col in ["senior_terms_found", "advanced_terms_found", "process_terms_found"]:
    preview_df[list_col] = preview_df[list_col].map(
        lambda values: ", ".join(values) if isinstance(values, list) else ""
    )

preview_df = preview_df.rename(
    columns={
        "issue_number": "numero_issue",
        "title": "titulo",
        "created_at": "criado_em",
        "difficulty_score": "indice_exigencia",
        "difficulty_class": "classe_exigencia",
        "years_required": "anos_experiencia_exigidos",
        "tech_count": "quantidade_tecnologias",
        "requires_english": "exige_ingles",
        "has_advanced_stack": "stack_avancada",
        "has_hard_process": "processo_seletivo_mais_exigente",
        "senior_terms_found": "termos_pleno_senior",
        "advanced_terms_found": "termos_stack_avancada",
        "process_terms_found": "termos_processo_exigente",
    }
)

preview_cols = [
    "numero_issue",
    "titulo",
    "criado_em",
    "indice_exigencia",
    "classe_exigencia",
    "anos_experiencia_exigidos",
    "quantidade_tecnologias",
    "exige_ingles",
    "stack_avancada",
    "processo_seletivo_mais_exigente",
    "termos_pleno_senior",
    "termos_stack_avancada",
    "termos_processo_exigente",
]
st.dataframe(preview_df[preview_cols].sort_values("criado_em", ascending=False).head(50), use_container_width=True)

csv_bytes = preview_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Baixar CSV da amostra analisada",
    data=csv_bytes,
    file_name=f"{owner}_{repo}_sample_features.csv",
    mime="text/csv",
)

loading_placeholder.empty()
status_placeholder.empty()
