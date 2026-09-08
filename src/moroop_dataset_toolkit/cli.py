"""Command-line interface for the MoRoOp dataset toolkit."""

from __future__ import annotations

import argparse
from pathlib import Path

from .data import download_from_huggingface, download_from_kth_repository
from .figures import (
    battery_state,
    driving_path,
    representative_gantt,
    representative_velocity,
)


def main() -> None:
    parser = argparse.ArgumentParser(prog="moroop")
    commands = parser.add_subparsers(dest="command", required=True)
    download = commands.add_parser("download", help="Download a dataset release.")
    download.add_argument("--source", choices=("huggingface", "kth"), required=True)
    download.add_argument("--destination", type=Path, required=True)
    download.add_argument("--revision", help="Hugging Face revision or release tag.")
    download.add_argument("--url", help="Direct KTH Data Repository ZIP URL.")
    figures = commands.add_parser("figures", help="Recreate all publication figures.")
    figures.add_argument("--data-directory", type=Path, required=True)
    figures.add_argument("--output-directory", type=Path, default=Path("figures"))
    args = parser.parse_args()
    if args.command == "download":
        if args.source == "huggingface":
            download_from_huggingface(args.destination, revision=args.revision)
        else:
            if not args.url:
                parser.error("--url is required when --source kth")
            download_from_kth_repository(args.url, args.destination)
        return
    args.output_directory.mkdir(parents=True, exist_ok=True)
    representative_gantt(
        args.data_directory,
        args.output_directory / "representative_operations_gantt.pdf",
    )
    representative_velocity(
        args.data_directory,
        args.output_directory / "representative_operations_velocity.pdf",
    )
    battery_state(
        args.data_directory, args.output_directory / "robot_battery_state.pdf"
    )
    driving_path(args.data_directory, args.output_directory / "robot_driving_path.pdf")


if __name__ == "__main__":
    main()
