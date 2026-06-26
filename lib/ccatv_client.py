from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request
import json
import re


_ID_PATTERN = re.compile(r"-(\d+)-\d{8}T\d{6}Z$")


@dataclass(frozen=True, slots=True)
class RecordingSummary:
    id: int
    output_path: str
    program_title: str | None
    description: str | None

    @property
    def basename(self) -> str:
        return Path(self.output_path).name


@dataclass(frozen=True, slots=True)
class LookupResult:
    recording: RecordingSummary | None
    recording_id: int | None


def extract_recording_id_from_filename(file_path: str) -> int | None:
    stem = Path(file_path).stem
    match = _ID_PATTERN.search(stem)
    if not match:
        return None
    return int(match.group(1))


def fetch_recordings(base_url: str, bearer_token: str | None = None) -> list[RecordingSummary]:
    api_url = f"{base_url.rstrip('/')}/api/recordings"
    req = request.Request(api_url, method="GET")
    if bearer_token:
        req.add_header("Authorization", f"Bearer {bearer_token}")

    try:
        with request.urlopen(req, timeout=20) as response:
            raw = response.read()
    except error.HTTPError as exc:
        raise RuntimeError(f"ccatv API returned HTTP {exc.code}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"unable to reach ccatv API: {exc.reason}") from exc

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid JSON from ccatv API: {exc}") from exc

    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise RuntimeError("ccatv API response did not indicate success")

    body = payload.get("payload")
    if not isinstance(body, dict):
        raise RuntimeError("ccatv API returned malformed payload")

    items = body.get("recordings")
    if not isinstance(items, list):
        raise RuntimeError("ccatv API returned malformed recordings list")

    results: list[RecordingSummary] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        rec_id = item.get("id")
        output_path = item.get("outputPath")
        if not isinstance(rec_id, int) or not isinstance(output_path, str):
            continue
        program_title = item.get("programTitle")
        description = item.get("description")
        results.append(
            RecordingSummary(
                id=rec_id,
                output_path=output_path,
                program_title=program_title if isinstance(program_title, str) else None,
                description=description if isinstance(description, str) else None,
            )
        )
    return results


def lookup_recording_for_path(
    *,
    file_path: str,
    recordings: list[RecordingSummary],
) -> LookupResult:
    basename = Path(file_path).name
    parsed_id = extract_recording_id_from_filename(file_path)

    exact = [r for r in recordings if Path(r.output_path).name == basename]
    if exact:
        if parsed_id is not None:
            with_id = [r for r in exact if r.id == parsed_id]
            if with_id:
                return LookupResult(recording=with_id[0], recording_id=parsed_id)
        return LookupResult(recording=exact[0], recording_id=parsed_id)

    if parsed_id is not None:
        for record in recordings:
            if record.id == parsed_id:
                return LookupResult(recording=record, recording_id=parsed_id)

    return LookupResult(recording=None, recording_id=parsed_id)
