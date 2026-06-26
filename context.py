from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote
import sys

import xbmc
import xbmcaddon
import xbmcgui

from lib.ccatv_client import fetch_recordings, lookup_recording_for_path
from lib.jellyfin import build_movie_destination, build_tv_destination, move_recording_with_sidecars
from lib.ui import ask_user_for_target


ADDON = xbmcaddon.Addon()
DIALOG = xbmcgui.Dialog()


def _log(message: str, level: int = xbmc.LOGINFO) -> None:
    xbmc.log(f"script.ccatv.jellyfin: {message}", level)


def _selected_file_path() -> Path | None:
    # Context menu scripts can access the selected item through ListItem.* labels.
    candidate = xbmc.getInfoLabel("ListItem.FileNameAndPath") or xbmc.getInfoLabel("ListItem.Path")
    if not candidate:
        return None

    if candidate.startswith("file://"):
        candidate = candidate[7:]
    candidate = unquote(candidate)

    return Path(candidate)


def _load_settings() -> dict[str, str]:
    return {
        "ccatv_base_url": ADDON.getSetting("ccatv_base_url").strip(),
        "ccatv_web_token": ADDON.getSetting("ccatv_web_token").strip(),
        "recordings_root": ADDON.getSetting("recordings_root").strip(),
        "movies_root": ADDON.getSetting("movies_root").strip(),
        "tv_root_comedy": ADDON.getSetting("tv_root_comedy").strip(),
        "tv_root_drama": ADDON.getSetting("tv_root_drama").strip(),
        "require_recording_id_match": ADDON.getSetting("require_recording_id_match").strip().lower(),
    }


def run() -> None:
    source_path = _selected_file_path()
    if source_path is None:
        DIALOG.notification("ccatv to Jellyfin", "No file selected", xbmcgui.NOTIFICATION_ERROR)
        return

    if not source_path.exists() or not source_path.is_file():
        DIALOG.notification("ccatv to Jellyfin", f"File not found: {source_path}", xbmcgui.NOTIFICATION_ERROR)
        return

    settings = _load_settings()
    recordings_root = Path(settings["recordings_root"]) if settings["recordings_root"] else None
    if recordings_root and recordings_root.exists():
        try:
            source_path.relative_to(recordings_root)
        except ValueError:
            DIALOG.notification(
                "ccatv to Jellyfin",
                "Selected file is outside configured ccatv root",
                xbmcgui.NOTIFICATION_ERROR,
            )
            return

    default_title = source_path.stem
    lookup = None
    base_url = settings["ccatv_base_url"]
    if base_url:
        try:
            recordings = fetch_recordings(base_url, settings["ccatv_web_token"] or None)
            lookup = lookup_recording_for_path(file_path=str(source_path), recordings=recordings)
        except Exception as exc:
            _log(f"recording lookup failed: {exc}", xbmc.LOGWARNING)

    if lookup and lookup.recording and lookup.recording.program_title:
        default_title = lookup.recording.program_title

    if settings["require_recording_id_match"] == "true" and (lookup is None or lookup.recording is None):
        DIALOG.notification(
            "ccatv to Jellyfin",
            "No matching ccatv recording found for selected file",
            xbmcgui.NOTIFICATION_ERROR,
        )
        return

    tv_roots = {
        "comedy": settings["tv_root_comedy"],
        "drama": settings["tv_root_drama"],
    }
    tv_roots = {name: Path(path) for name, path in tv_roots.items() if path.strip()}

    selection = ask_user_for_target(
        default_title=default_title,
        source_path=source_path,
        tv_root_names=list(tv_roots.keys()),
    )
    if selection is None:
        return

    if selection.media_type == "movie":
        movies_root = Path(settings["movies_root"])
        destination = build_movie_destination(
            movies_root=movies_root,
            title=selection.title,
            year=selection.year,
            source_path=source_path,
        )
    else:
        if selection.tv_root_name is None:
            DIALOG.notification("ccatv to Jellyfin", "No TV root selected", xbmcgui.NOTIFICATION_ERROR)
            return
        tv_root = tv_roots[selection.tv_root_name]
        destination = build_tv_destination(
            tv_root=tv_root,
            title=selection.title,
            year=selection.year,
            season_number=selection.season_number or 1,
            episode_number=selection.episode_number or 1,
            source_path=source_path,
        )

    confirm = DIALOG.yesno(
        "Move recording",
        f"Source: {source_path}\n\nDestination: {destination}",
        yeslabel="Move",
        nolabel="Cancel",
    )
    if not confirm:
        return

    try:
        moved = move_recording_with_sidecars(source_path, destination)
    except Exception as exc:
        _log(f"move failed: {exc}", xbmc.LOGERROR)
        DIALOG.notification("ccatv to Jellyfin", f"Move failed: {exc}", xbmcgui.NOTIFICATION_ERROR)
        return

    _log(f"moved {len(moved)} files to {destination.parent}")
    DIALOG.notification(
        "ccatv to Jellyfin",
        f"Moved {len(moved)} file(s) to {destination.parent}",
        xbmcgui.NOTIFICATION_INFO,
    )


if __name__ == "__main__":
    del sys.argv
    run()
