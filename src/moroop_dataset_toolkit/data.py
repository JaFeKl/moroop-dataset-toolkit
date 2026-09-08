"""Download and load MoRoOp Parquet data."""

from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

DEFAULT_HF_REPOSITORY = "Self-Organizing-Production-Logistics/mobile_robot_operations"
TABLE_NAMES = {
    "jobs",
    "operations",
    "dispatch_events",
    "robot_state_raw",
    "robot_state_cleaned",
    "kits",
}


def download_from_huggingface(
    destination: str | Path,
    *,
    repository: str = DEFAULT_HF_REPOSITORY,
    revision: str | None = None,
    token: str | None = None,
) -> Path:
    """Download a MoRoOp snapshot from the Hugging Face Hub.

    Set ``revision`` to a release tag such as ``1.0.0`` for a reproducible copy.
    """
    from huggingface_hub import snapshot_download

    destination = Path(destination)
    snapshot_download(
        repo_id=repository,
        repo_type="dataset",
        revision=revision,
        token=token,
        local_dir=destination,
    )
    return destination


def download_from_kth_repository(
    destination: str | Path,
    archive_url: str = "https://datarepository.kth.se/records/0qdea-h5385/files/MoRoOp_V_1_0_0.zip",
) -> Path:
    """Download and extract a ZIP archive from the KTH Data Repository.

    Pass the repository's direct ZIP download URL as ``archive_url``. The archive
    is retained as ``moroop-dataset.zip`` in the destination directory.
    """
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / "moroop-dataset.zip"
    with (
        urllib.request.urlopen(archive_url) as response,
        archive_path.open("wb") as file,
    ):
        shutil.copyfileobj(response, file)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(destination)
    return destination


def load_table(
    data_directory: str | Path,
    table: str,
    *,
    shift: str | None = None,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Load a MoRoOp Parquet table into a pandas dataframe.

    ``kits`` is shared across shifts and must be loaded without ``shift``. All
    other tables require a shift identifier such as ``2026_07_27_evening``.
    """
    if table not in TABLE_NAMES:
        raise ValueError(
            f"Unknown table {table!r}. Expected one of {sorted(TABLE_NAMES)}."
        )

    data_directory = Path(data_directory)
    if table == "kits":
        if shift is not None:
            raise ValueError(
                "The shared kits table does not have shift-specific files."
            )
        path = data_directory / "kits.parquet"
    else:
        if shift is None:
            raise ValueError(f"A shift is required to load the {table!r} table.")
        path = data_directory / shift / f"{shift}_{table}.parquet"

    if not path.is_file():
        raise FileNotFoundError(f"Dataset table not found: {path}")
    return pd.read_parquet(path, columns=columns)
