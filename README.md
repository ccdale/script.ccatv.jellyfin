# script.ccatv.jellyfin

Kodi context-menu addon that moves ccatv recording files into Jellyfin-friendly folder structures.

## What it does

- Adds a context menu item: **Move recording to Jellyfin**
- Uses filename/job-id matching (and optional ccatv API lookup) to prefill title
- Prompts for:
  - Movie vs TV series
  - Title and year (`Title (Year)` folder convention)
  - For TV: destination root (`comedy` or `drama`) and season/episode numbers
- Moves the selected recording file and all same-stem sidecars together
  - Includes `.nfo`, `.edl`, `.txt`, and other same-stem files (for comskip outputs)
- Movies are placed under an A-Z letter folder, ignoring leading articles (`a`, `an`, `the`)
  - Example: `The Prisoner of Zenda (1937)` -> `.../Films/P/The Prisoner of Zenda (1937)/`

## Default paths

- ccatv source root: `/mnt/nas/ccatv`
- Jellyfin movies: `/mnt/nas/Video/Films`
- Jellyfin TV roots:
  - `/mnt/nas/Video/comedy`
  - `/mnt/nas/Video/drama`

All paths are configurable in addon settings.

## ccatv integration

This addon is designed to work with [ccatv](https://github.com/ccdale/ccatv).

It can call ccatv web API `/api/recordings` (with optional bearer token) to get better default titles.

## Install for development

1. Copy this folder into Kodi addons path as `script.ccatv.jellyfin`.
2. Enable the addon in Kodi.
3. Open addon settings and set API/token/path values for your environment.
4. Right-click a recording under your ccatv source path and select **Move recording to Jellyfin**.

## Notes

- The addon intentionally does not scrape TMDB/TVDB. It focuses on correct naming, then Jellyfin scrapers handle metadata/art.
- If destination filename already exists, a numeric suffix is appended.
