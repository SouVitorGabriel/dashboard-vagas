from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.features import build_features
from src.github_issues import fetch_issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a small GitHub issues sample and save engineered features."
    )
    parser.add_argument("--owner", default="backend-br", help="GitHub repository owner")
    parser.add_argument("--repo", default="vagas", help="GitHub repository name")
    parser.add_argument("--state", default="all", choices=["all", "open", "closed"])
    parser.add_argument("--limit", type=int, default=100, help="Max issues to fetch")
    parser.add_argument(
        "--output",
        default="data/issues_sample_features.csv",
        help="Output CSV file path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = fetch_issues(
        owner=args.owner,
        repo=args.repo,
        state=args.state,
        limit=args.limit,
    )
    raw_df = pd.DataFrame(payload)
    features_df = build_features(raw_df)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_path, index=False)

    print(f"Saved {len(features_df)} rows to {output_path}")


if __name__ == "__main__":
    main()
