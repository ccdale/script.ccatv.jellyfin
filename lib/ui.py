from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence
import xml.etree.ElementTree as ET

import xbmcgui


@dataclass(frozen=True, slots=True)
class UserSelection:
    media_type: str
    title: str
    year: int
    season_number: int | None
    episode_number: int | None
    tv_root_name: str | None


def _read_nfo_year(path: Path) -> int | None:
    nfo = path.with_suffix(".nfo")
    if not nfo.is_file():
        return None
    try:
        root = ET.parse(nfo).getroot()
    except (ET.ParseError, OSError):
        return None

    for tag in ("year", "premiered", "aired"):
        node = root.find(f".//{tag}")
        if node is None or not node.text:
            continue
        text = node.text.strip()
        if len(text) >= 4 and text[:4].isdigit():
            return int(text[:4])
    return None


def ask_user_for_target(
    *,
    default_title: str,
    source_path: Path,
    tv_root_names: Sequence[str],
) -> UserSelection | None:
    dialog = xbmcgui.Dialog()

    media_idx = dialog.select("Move as", ["Movie", "TV series"])
    if media_idx < 0:
        return None
    media_type = "movie" if media_idx == 0 else "tv"

    title = dialog.input("Title", defaultt=default_title)
    if not title.strip():
        dialog.notification("ccatv to Jellyfin", "Title is required", xbmcgui.NOTIFICATION_ERROR)
        return None

    suggested_year = _read_nfo_year(source_path) or datetime.now().year
    year_text = dialog.input("Year", defaultt=str(suggested_year), type=xbmcgui.INPUT_NUMERIC)
    if not year_text.strip().isdigit():
        dialog.notification("ccatv to Jellyfin", "Year must be numeric", xbmcgui.NOTIFICATION_ERROR)
        return None
    year = int(year_text)

    if media_type == "movie":
        return UserSelection(
            media_type=media_type,
            title=title.strip(),
            year=year,
            season_number=None,
            episode_number=None,
            tv_root_name=None,
        )

    if not tv_root_names:
        dialog.notification("ccatv to Jellyfin", "No TV roots configured", xbmcgui.NOTIFICATION_ERROR)
        return None

    root_idx = dialog.select("TV folder", list(tv_root_names))
    if root_idx < 0:
        return None
    root_name = tv_root_names[root_idx]

    season_text = dialog.input("Season number", defaultt="1", type=xbmcgui.INPUT_NUMERIC)
    episode_text = dialog.input("Episode number", defaultt="1", type=xbmcgui.INPUT_NUMERIC)
    if not season_text.strip().isdigit() or not episode_text.strip().isdigit():
        dialog.notification(
            "ccatv to Jellyfin",
            "Season and episode numbers must be numeric",
            xbmcgui.NOTIFICATION_ERROR,
        )
        return None

    return UserSelection(
        media_type=media_type,
        title=title.strip(),
        year=year,
        season_number=int(season_text),
        episode_number=int(episode_text),
        tv_root_name=root_name,
    )
