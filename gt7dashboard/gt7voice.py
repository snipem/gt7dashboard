"""Spoken lap announcements.

The telemetry thread calls LapAnnouncer once for each stored lap.
Speech is the macOS `say` command, launched and not waited on, so packet
collection keeps running. `GT7_LAP_ANNOUNCE=false` silences every announcement,
including the Test Voice button. `GT7_LAP_VOICE` selects the macOS voice and
defaults to Daniel.
"""

import logging
import os
import shutil
import subprocess
from typing import List, Optional, Sequence

from gt7dashboard.gt7lap import Lap

logger = logging.getLogger(__name__)

DEFAULT_LAP_VOICE = "Daniel"

SAMPLE_LAP_NUMBER = 4
SAMPLE_LAP_TIME_MS = 93653
SAMPLE_PREVIOUS_BEST_MS = 92472


def _spoken_duration(duration_ms: int) -> str:
    duration_ms = abs(int(duration_ms))
    minutes = duration_ms // 60000
    remainder_ms = duration_ms % 60000
    seconds = f"{remainder_ms // 1000}.{remainder_ms % 1000:03d}"
    if minutes == 0:
        return f"{seconds} seconds"
    minute_word = "minute" if minutes == 1 else "minutes"
    return f"{minutes} {minute_word} {seconds} seconds"


def format_lap_announcement(
    lap_number: int, lap_time_ms: int, previous_best_ms: Optional[int]
) -> str:
    """Build the sentence spoken for one completed lap.

    previous_best_ms is the fastest valid lap already stored before this one.
    None means this is the first completed lap of the session.
    """
    lap_time = _spoken_duration(lap_time_ms)
    if previous_best_ms is None:
        comparison = "First completed lap."
    elif lap_time_ms < previous_best_ms:
        delta = _spoken_duration(previous_best_ms - lap_time_ms)
        comparison = (
            f"Faster than your previous best by {delta}. New fastest lap."
        )
    elif lap_time_ms > previous_best_ms:
        delta = _spoken_duration(lap_time_ms - previous_best_ms)
        comparison = f"Slower than your fastest lap by {delta}."
    else:
        comparison = "Matching your fastest lap."
    return f"Lap {lap_number}. Time {lap_time}. {comparison}"


def sample_announcement() -> str:
    """The fixed sentence used by the Test Voice button."""
    return format_lap_announcement(
        SAMPLE_LAP_NUMBER, SAMPLE_LAP_TIME_MS, SAMPLE_PREVIOUS_BEST_MS
    )


def _announcements_enabled() -> bool:
    return os.environ.get("GT7_LAP_ANNOUNCE", "true").lower() != "false"


def _lap_voice() -> str:
    voice = os.environ.get("GT7_LAP_VOICE", DEFAULT_LAP_VOICE).strip()
    return voice or DEFAULT_LAP_VOICE


def speak(text: str) -> None:
    """Speak text without blocking the caller. No-op when speech is unavailable."""
    if not text or not _announcements_enabled():
        return

    say = shutil.which("say")
    if say is None:
        logger.info("Lap announcement not spoken; macOS say command was not found")
        return

    logger.info("Lap announcement: %s", text)
    try:
        subprocess.Popen(
            [say, "-v", _lap_voice(), text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        logger.exception("Failed to start lap announcement")


def play_sample_announcement() -> None:
    """Speak the sample line. Does not read or write lap data."""
    speak(sample_announcement())


def _valid_lap(lap: Lap) -> bool:
    return (
        not lap.is_replay
        and lap.lap_finish_time > 0
        and len(lap.data_speed) > 0
    )


def announcement_for_completed_lap(
    lap: Lap, previous_laps: Sequence[Lap]
) -> Optional[str]:
    """Return the sentence for a lap that finish_lap has already stored.

    previous_laps must be the session laps stored before this one, newest first
    or in any order. Replay laps and laps the app already rejected are skipped.
    """
    if not _valid_lap(lap):
        return None

    previous_times = [
        earlier.lap_finish_time for earlier in previous_laps if _valid_lap(earlier)
    ]
    previous_best = min(previous_times) if previous_times else None
    return format_lap_announcement(lap.number, lap.lap_finish_time, previous_best)


class LapAnnouncer:
    """One announcement per stored lap. Safe to call from the telemetry thread."""

    def __init__(self, laps_provider):
        self._laps_provider = laps_provider
        self._last_spoken = None

    def on_lap(self, lap: Lap) -> None:
        # finish_lap inserts the new lap at index 0 before invoking the callback.
        key = (lap.number, lap.lap_finish_time, lap.lap_end_timestamp)
        if key == self._last_spoken:
            return

        laps: List[Lap] = self._laps_provider() or []
        previous = laps[1:] if laps else []
        text = announcement_for_completed_lap(lap, previous)
        if text is None:
            return

        self._last_spoken = key
        speak(text)
