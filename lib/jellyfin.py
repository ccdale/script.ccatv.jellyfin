from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil


@dataclass(frozen=True, slots=True)
class MovePlan:
    media_type: str
    title: str
    year: int
    source_path: Path
    destination_main_path: Path


def sanitize_component(value: str, fallback: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._ -]+", " ", value).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.strip(" .")
    return normalized or fallback


def build_movie_destination(*, movies_root: Path, title: str, year: int, source_path: Path) -> Path:
    safe_title = sanitize_component(title, fallback="Untitled")
    folder = f"{safe_title} ({year})"
    filename = f"{safe_title} ({year}){source_path.suffix}"
    return movies_root / folder / filename


def build_tv_destination(
    *,
    tv_root: Path,
    title: str,
    year: int,
    season_number: int,
    episode_number: int,
    source_path: Path,
) -> Path:
    safe_title = sanitize_component(title, fallback="Untitled")
    show_folder = f"{safe_title} ({year})"
    season_folder = f"Season {season_number:02d}"
    filename = f"{safe_title} ({year}) - s{season_number:02d}e{episode_number:02d}{source_path.suffix}"
    return tv_root / show_folder / season_folder / filename


def collect_related_files(source_path: Path) -> list[Path]:
    if not source_path.parent.exists():
        return []
    related = [
        candidate
        for candidate in source_path.parent.iterdir()
        if candidate.is_file() and candidate.stem == source_path.stem
    ]
    related.sort(key=lambda p: p.name)
    return related


def next_available_destination(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = path.with_name(f"{stem}-{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def move_recording_with_sidecars(source_path: Path, destination_main_path: Path) -> list[tuple[Path, Path]]:
    files = collect_related_files(source_path)
    if not files:
        raise RuntimeError(f"no source files found for {source_path}")

    destination_main_path.parent.mkdir(parents=True, exist_ok=True)
    moved: list[tuple[Path, Path]] = []

    main_target = next_available_destination(destination_main_path)
    for file_path in files:
        if file_path == source_path:
            target = main_target
        else:
            # Keep sidecar extension but rename stem to match the moved main file.
            target = main_target.with_suffix(file_path.suffix)
            target = next_available_destination(target)

        shutil.move(str(file_path), str(target))
        moved.append((file_path, target))

    return moved
