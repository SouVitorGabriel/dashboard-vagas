from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Dict, Sequence, Set

import pandas as pd

JUNIOR_TERMS = [
    "junior",
    "jr",
    "trainee",
    "estagio",
    "estagiario",
    "entry level",
]

SENIOR_TERMS = ["pleno", "senior", "especialista", "staff", "lead"]

PT_HINT_WORDS = {
    "de",
    "para",
    "com",
    "que",
    "uma",
    "vaga",
    "requisitos",
    "conhecimento",
    "experiencia",
    "desejavel",
    "atuar",
    "empresa",
    "desenvolvimento",
    "backend",
    "brasil",
    "remoto",
    "beneficios",
    "salario",
    "time",
}

TECH_PATTERNS: Dict[str, Sequence[str]] = {
    "python": ["python"],
    "java": ["java"],
    "javascript": ["javascript", "js", "node", "nodejs"],
    "typescript": ["typescript", "ts"],
    "php": ["php"],
    "go": [" golang", "go lang", " go "],
    "dotnet": [".net", "dotnet", "c#", "csharp"],
    "sql": ["sql", "postgres", "mysql", "oracle"],
    "nosql": ["mongodb", "redis", "dynamodb", "cassandra"],
    "cloud": ["aws", "azure", "gcp", "cloud"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "git": ["git", "github", "gitlab"],
    "rest": ["rest", "api rest"],
    "microservices": ["microservices", "microservicos"],
    "ci_cd": ["ci/cd", "cicd", "pipeline"],
}

ADVANCED_TERMS = [
    "arquitetura",
    "kubernetes",
    "k8s",
    "microservicos",
    "microservices",
    "mensageria",
    "event driven",
    "clean architecture",
    "ddd",
    "system design",
]

PROCESS_HARD_TERMS = [
    "live coding",
    "desafio tecnico",
    "teste tecnico",
    "case tecnico",
    "pair programming",
    "multiplas etapas",
    "painel tecnico",
]

ENGLISH_TERMS = ["ingles", "english", "fluente", "intermediario", "avancado"]

YEARS_PATTERN = re.compile(
    r"(\d{1,2})\s*\+?\s*(?:anos?|ano|years?)\s*(?:de)?\s*(?:experiencia|experience|exp)?"
)


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_text(value: str) -> str:
    if not value:
        return ""
    text = strip_accents(str(value)).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def has_any_term(text: str, terms: Sequence[str]) -> bool:
    return any(term in text for term in terms)


def extract_years_required(text: str) -> int:
    matches = YEARS_PATTERN.findall(text)
    if not matches:
        return 0

    values = [int(match) for match in matches if match.isdigit()]
    if not values:
        return 0

    return int(min(20, max(values)))


def extract_tech_set(text: str) -> Set[str]:
    found: Set[str] = set()
    padded_text = f" {text} "

    for tech_name, hints in TECH_PATTERNS.items():
        if any(hint in padded_text for hint in hints):
            found.add(tech_name)

    return found


def looks_portuguese(text: str) -> bool:
    tokens = re.findall(r"[a-z]{2,}", text)
    if not tokens:
        return False

    hits = sum(token in PT_HINT_WORDS for token in tokens)
    ratio = hits / max(1, len(tokens))

    if len(tokens) < 15:
        return hits >= 2

    return hits >= 3 and ratio >= 0.03


def is_junior_posting(text: str, labels: Sequence[str]) -> bool:
    labels_joined = " ".join(labels)
    combined = f" {text} {labels_joined} "
    return has_any_term(combined, JUNIOR_TERMS)


def classify_difficulty(score: float) -> str:
    if score <= 2.0:
        return "baixo"
    if score <= 4.0:
        return "medio"
    return "alto"


def build_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return raw_df.copy()

    df = raw_df.copy()
    df["title"] = df["title"].fillna("")
    df["body"] = df["body"].fillna("")
    df["labels"] = df["labels"].apply(lambda value: value if isinstance(value, list) else [])

    df["text"] = (df["title"] + "\n" + df["body"]).astype(str)
    df["text_norm"] = df["text"].map(normalize_text)
    df["labels_norm"] = df["labels"].apply(lambda value: [normalize_text(str(item)) for item in value])

    df["is_junior"] = df.apply(
        lambda row: is_junior_posting(row["text_norm"], row["labels_norm"]), axis=1
    )
    df["is_portuguese"] = df["text_norm"].map(looks_portuguese)

    df["years_required"] = df["text_norm"].map(extract_years_required)

    df["tech_list"] = df["text_norm"].map(lambda text: sorted(extract_tech_set(text)))
    df["tech_count"] = df["tech_list"].map(len)

    df["requires_english"] = df["text_norm"].map(lambda text: has_any_term(text, ENGLISH_TERMS))
    df["has_advanced_stack"] = df["text_norm"].map(
        lambda text: has_any_term(text, ADVANCED_TERMS)
    )
    df["has_hard_process"] = df["text_norm"].map(
        lambda text: has_any_term(text, PROCESS_HARD_TERMS)
    )
    df["mentions_senior_terms"] = df["text_norm"].map(
        lambda text: has_any_term(text, SENIOR_TERMS)
    )
    df["senior_mismatch"] = df["is_junior"] & df["mentions_senior_terms"]

    df["difficulty_score"] = (
        (df["years_required"] >= 2).astype(float) * 2.0
        + df["requires_english"].astype(float) * 1.5
        + df["tech_count"].clip(upper=4).astype(float) * 0.5
        + df["has_advanced_stack"].astype(float) * 1.0
        + df["has_hard_process"].astype(float) * 1.0
        + df["senior_mismatch"].astype(float) * 1.0
    )
    df["difficulty_class"] = df["difficulty_score"].map(classify_difficulty)

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce", utc=True)

    return df


def tech_frequency(df: pd.DataFrame) -> pd.DataFrame:
    counter: Counter[str] = Counter()
    if "tech_list" not in df.columns:
        return pd.DataFrame(columns=["tech", "count"])

    for techs in df["tech_list"].tolist():
        for tech in techs:
            counter[tech] += 1

    items = sorted(counter.items(), key=lambda item: item[1], reverse=True)
    return pd.DataFrame(items, columns=["tech", "count"])


def hard_signal_overview(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["signal", "rate"])

    rows = [
        ("Exige ingles", df["requires_english"].mean()),
        ("Stack avancada", df["has_advanced_stack"].mean()),
        ("Processo seletivo mais exigente", df["has_hard_process"].mean()),
        ("Mismatch junior/pleno-senior", df["senior_mismatch"].mean()),
    ]
    out = pd.DataFrame(rows, columns=["signal", "rate"])
    out["rate"] = out["rate"].fillna(0.0)
    return out
