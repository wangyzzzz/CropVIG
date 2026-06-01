from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_Y_PATH = REPO_ROOT / "data/processed/model_inputs_engineered/gdd_rel_heading/y.parquet"
DEFAULT_BACKUP_PATH = REPO_ROOT / "data/processed/model_inputs_engineered/gdd_rel_heading/y.before_quality_traits.parquet"

QUALITY_FILES = {
    2022: REPO_ROOT / "data/raw/21-22品质.xlsx",
    2024: REPO_ROOT / "data/raw/23-24品质.xlsx",
    2025: REPO_ROOT / "data/raw/24-25品质.xlsx",
}

QUALITY_PREFIX = {
    2022: "22YLG_",
    2024: "24YLG_",
    2025: "25YLG_",
}

TARGET_TRAITS = ("CPM", "Water")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge CPM/Water into current CropHG y.parquet using current analysis samples only.")
    parser.add_argument("--y-path", type=str, default=str(DEFAULT_Y_PATH), help="Existing y.parquet path.")
    parser.add_argument(
        "--backup-path",
        type=str,
        default=str(DEFAULT_BACKUP_PATH),
        help="Backup path written once before overwrite.",
    )
    parser.add_argument("--write", action="store_true", help="Actually overwrite y.parquet.")
    return parser


def _load_quality_table(year: int, path: Path) -> pd.DataFrame:
    df = pd.read_excel(path).copy()
    df["plot_id"] = df["编号"].astype(str)
    df["year"] = int(year)
    df["Number"] = df["Number"].astype(str)
    prefix = QUALITY_PREFIX[year]
    rename_map = {f"{prefix}{trait}": trait for trait in TARGET_TRAITS if f"{prefix}{trait}" in df.columns}
    keep_cols = ["plot_id", "year", "Number"] + list(rename_map.keys())
    out = df.loc[:, [c for c in keep_cols if c in df.columns]].copy()
    out = out.rename(columns=rename_map)
    return out


def build_quality_merge_frame() -> pd.DataFrame:
    frames = [_load_quality_table(year, path) for year, path in QUALITY_FILES.items()]
    out = pd.concat(frames, ignore_index=True, sort=False)
    out = out.drop_duplicates(subset=["plot_id", "year"], keep="first").copy()
    return out


def merge_quality_traits(y_df: pd.DataFrame, quality_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = y_df.copy()
    work["plot_id"] = work["plot_id"].astype(str)
    work["year"] = pd.to_numeric(work["year"], errors="raise").astype(int)
    for trait in TARGET_TRAITS:
        if trait in work.columns:
            work = work.drop(columns=[trait])
    merged = work.merge(quality_df[["plot_id", "year", *TARGET_TRAITS]], on=["plot_id", "year"], how="left")
    summary = (
        merged.groupby("year")[list(TARGET_TRAITS)]
        .apply(lambda x: x.notna().sum())
        .reset_index()
    )
    return merged, summary


def main() -> None:
    args = build_parser().parse_args()
    y_path = Path(args.y_path)
    backup_path = Path(args.backup_path)

    y_df = pd.read_parquet(y_path)
    quality_df = build_quality_merge_frame()
    merged, summary = merge_quality_traits(y_df, quality_df)

    print(f"y rows: {len(merged)}")
    print(f"matched CPM: {int(merged['CPM'].notna().sum())}")
    print(f"matched Water: {int(merged['Water'].notna().sum())}")
    print(summary.to_string(index=False))

    if not args.write:
        print("dry-run only; pass --write to overwrite y.parquet")
        return

    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists():
        y_df.to_parquet(backup_path, index=False)
    merged.to_parquet(y_path, index=False)
    print(f"wrote: {y_path}")
    print(f"backup: {backup_path}")


if __name__ == "__main__":
    main()
