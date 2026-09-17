from pathlib import Path

from moroop_dataset_toolkit import cli


def test_kth_download_forwards_destination_and_url(monkeypatch) -> None:
    captured: dict[str, Path | str] = {}

    def download(destination: Path, archive_url: str) -> None:
        captured["destination"] = destination
        captured["archive_url"] = archive_url

    monkeypatch.setattr(cli, "download_from_kth_repository", download)
    monkeypatch.setattr(
        "sys.argv",
        [
            "moroop",
            "download",
            "--source",
            "kth",
            "--destination",
            "data/moroop",
            "--url",
            "https://example.test/moroop.zip",
        ],
    )

    cli.main()

    assert captured == {
        "destination": Path("data/moroop"),
        "archive_url": "https://example.test/moroop.zip",
    }from pathlib import Path

from moroop_dataset_toolkit import cli


def test_huggingface_download_forwards_token(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def download(destination: Path, **kwargs: object) -> None:
        captured["destination"] = destination
        captured.update(kwargs)

    monkeypatch.setattr(cli, "download_from_huggingface", download)
    monkeypatch.setattr(
        "sys.argv",
        [
            "moroop",
            "download",
            "--source",
            "huggingface",
            "--destination",
            "data/moroop",
            "--revision",
            "1.0.1",
            "--token",
            "hf_example",
        ],
    )

    cli.main()

    assert captured == {
        "destination": Path("data/moroop"),
        "revision": "1.0.1",
        "token": "hf_example",
    }