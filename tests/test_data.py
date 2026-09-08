from pathlib import Path

import pandas as pd
import pytest

from moroop_dataset_toolkit.data import load_table


def test_load_shift_table(tmp_path: Path) -> None:
    shift = "2026_07_27_morning"
    shift_directory = tmp_path / shift
    shift_directory.mkdir()
    expected = pd.DataFrame({"id": [1], "created_at": ["2026-07-27T06:00:00Z"]})
    expected.to_parquet(shift_directory / f"{shift}_jobs.parquet", index=False)

    actual = load_table(tmp_path, "jobs", shift=shift)

    pd.testing.assert_frame_equal(actual, expected)


def test_load_kits_table(tmp_path: Path) -> None:
    expected = pd.DataFrame({"kit_id": ["K001"], "color": ["red"]})
    expected.to_parquet(tmp_path / "kits.parquet", index=False)

    actual = load_table(tmp_path, "kits")

    pd.testing.assert_frame_equal(actual, expected)


def test_shift_is_required_for_shift_tables(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="shift is required"):
        load_table(tmp_path, "jobs")
