from pathlib import Path

import pytest

from models.common.split_loader import load_split_groups


def test_split_loader_supports_migrated_four_scenarios() -> None:
    split_dir = Path('data/processed/splits_4scenarios')

    ref = load_split_groups(split_dir, validation_scenario='reference')
    ws = load_split_groups(split_dir, validation_scenario='within_season')
    loso = load_split_groups(split_dir, validation_scenario='loso')
    loso_geno = load_split_groups(split_dir, validation_scenario='loso_genotype')

    assert ref
    assert ws
    assert loso
    assert loso_geno
    assert (2022, 0) in ref
    assert (2022, 0) in ws
    assert (2022, 0) in loso
    assert (2022, 0) in loso_geno


def test_split_loader_fails_fast_for_missing_split_dir(tmp_path: Path) -> None:
    missing_dir = tmp_path / "missing_splits"

    with pytest.raises(FileNotFoundError, match="split_dir 不存在"):
        load_split_groups(missing_dir, validation_scenario="reference")


def test_split_loader_fails_fast_for_empty_scenario_dir(tmp_path: Path) -> None:
    empty_dir = tmp_path / "splits"
    empty_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="没有找到可用于 reference"):
        load_split_groups(empty_dir, validation_scenario="reference")
