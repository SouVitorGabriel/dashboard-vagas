from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression, LogisticRegression

MIN_CLUSTER_SAMPLE = 18
MIN_TERMS_SAMPLE = 30

CUSTOM_STOPWORDS = {
    "de",
    "da",
    "do",
    "das",
    "dos",
    "para",
    "com",
    "que",
    "uma",
    "um",
    "na",
    "no",
    "em",
    "e",
    "o",
    "a",
    "as",
    "os",
    "ser",
    "ter",
    "sobre",
    "vaga",
    "vagas",
    "junior",
    "jr",
    "backend",
    "empresa",
    "descricao",
    "requisitos",
    "beneficios",
    "remoto",
    "hibrido",
    "presencial",
    "clt",
    "pj",
    "vaga",
    "candidate",
    "candidatura",
    "informacoes",
    "informacao",
    "informar",
    "labels",
    "time",
    "dias",
    "anos",
    "ano",
    "brasil",
    "paulo",
    "sao",
    "https",
    "http",
    "linkedin",
}


def build_time_series(df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "period",
                "avg_difficulty",
                "median_difficulty",
                "n_jobs",
                "hard_process_rate",
                "english_rate",
            ]
        )

    working = df.dropna(subset=["created_at"]).copy()
    if working.empty:
        return pd.DataFrame(
            columns=[
                "period",
                "avg_difficulty",
                "median_difficulty",
                "n_jobs",
                "hard_process_rate",
                "english_rate",
            ]
        )

    working["period"] = working["created_at"].dt.to_period(freq).dt.to_timestamp()

    ts = (
        working.groupby("period", as_index=False)
        .agg(
            avg_difficulty=("difficulty_score", "mean"),
            median_difficulty=("difficulty_score", "median"),
            n_jobs=("issue_id", "count"),
            hard_process_rate=("has_hard_process", "mean"),
            english_rate=("requires_english", "mean"),
        )
        .sort_values("period")
    )

    return ts


def analyze_trend(ts_df: pd.DataFrame) -> Dict[str, float | str]:
    if ts_df.empty or len(ts_df) < 2:
        return {
            "direction": "insuficiente",
            "slope": 0.0,
            "r2": 0.0,
            "delta_pct": 0.0,
        }

    x = np.arange(len(ts_df), dtype=float).reshape(-1, 1)
    y = ts_df["avg_difficulty"].astype(float).values

    model = LinearRegression()
    model.fit(x, y)

    slope = float(model.coef_[0])
    r2 = float(model.score(x, y))

    first = y[0]
    last = y[-1]
    if first == 0:
        delta_pct = 0.0
    else:
        delta_pct = float((last - first) / abs(first) * 100.0)

    if slope > 0.03:
        direction = "aumento"
    elif slope < -0.03:
        direction = "queda"
    else:
        direction = "estavel"

    return {"direction": direction, "slope": slope, "r2": r2, "delta_pct": delta_pct}


def _vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        max_features=1500,
        min_df=2,
        max_df=0.9,
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b[a-z][a-z\+\#]{2,}\b",
        stop_words=list(CUSTOM_STOPWORDS),
    )


def cluster_texts(
    df: pd.DataFrame, n_clusters: int = 3
) -> Optional[Tuple[pd.DataFrame, pd.DataFrame]]:
    if df.empty or len(df) < max(MIN_CLUSTER_SAMPLE, n_clusters * 3):
        return None

    vect = _vectorizer()
    text_col = "text_ml" if "text_ml" in df.columns else "text_norm"
    matrix = vect.fit_transform(df[text_col].fillna(""))

    if matrix.shape[1] < 2:
        return None

    effective_clusters = min(n_clusters, len(df))
    model = KMeans(n_clusters=effective_clusters, random_state=42, n_init="auto")
    labels = model.fit_predict(matrix)

    reducer = TruncatedSVD(n_components=2, random_state=42)
    coords = reducer.fit_transform(matrix)

    cluster_df = df[["issue_id", "issue_number", "title", "difficulty_score", "created_at", "url"]].copy()
    cluster_df["cluster"] = labels.astype(str)
    cluster_df["x"] = coords[:, 0]
    cluster_df["y"] = coords[:, 1]

    feature_names = np.array(vect.get_feature_names_out())
    top_rows = []

    for cluster_index in range(effective_clusters):
        center = model.cluster_centers_[cluster_index]
        top_idx = np.argsort(center)[-10:][::-1]
        top_terms = [feature_names[i] for i in top_idx]
        top_rows.append({"cluster": str(cluster_index), "top_terms": ", ".join(top_terms)})

    top_terms_df = pd.DataFrame(top_rows)
    return cluster_df, top_terms_df


def difficulty_terms(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    if df.empty or len(df) < MIN_TERMS_SAMPLE:
        return None

    target = (df["difficulty_score"] >= df["difficulty_score"].median()).astype(int)
    if target.nunique() < 2:
        return None

    vect = _vectorizer()
    text_col = "text_ml" if "text_ml" in df.columns else "text_norm"
    matrix = vect.fit_transform(df[text_col].fillna(""))
    if matrix.shape[1] < 5:
        return None

    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(matrix, target)

    coefs = model.coef_[0]
    names = np.array(vect.get_feature_names_out())

    pos_idx = np.argsort(coefs)[-12:][::-1]
    neg_idx = np.argsort(coefs)[:12]

    rows = []
    for idx in pos_idx:
        rows.append({"term": names[idx], "coef": float(coefs[idx]), "direction": "mais exigente"})
    for idx in neg_idx:
        rows.append({"term": names[idx], "coef": float(coefs[idx]), "direction": "menos exigente"})

    terms_df = pd.DataFrame(rows).sort_values("coef", ascending=False)
    return terms_df
