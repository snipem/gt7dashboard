import subprocess
import unittest
from datetime import datetime
from unittest import mock

import gt7dashboard.gt7helper  # noqa: F401  (import before gt7lap; those modules import each other)
from gt7dashboard.gt7lap import Lap
from gt7dashboard.gt7voice import (
    LapAnnouncer,
    announcement_for_completed_lap,
    format_lap_announcement,
    play_sample_announcement,
    sample_announcement,
    speak,
)


def _lap(number, time_ms, replay=False, speed=True):
    lap = Lap()
    lap.number = number
    lap.lap_finish_time = time_ms
    lap.data_speed = [100] if speed else []
    lap.is_replay = replay
    lap.lap_end_timestamp = datetime(2026, 1, 1, 0, 0, number)
    return lap


class TestLapAnnouncementText(unittest.TestCase):
    def test_first_lap(self):
        self.assertEqual(
            format_lap_announcement(1, 99214, None),
            "Lap 1. Time 1 minute 39.214 seconds. First completed lap.",
        )

    def test_new_fastest_lap(self):
        self.assertEqual(
            format_lap_announcement(3, 92472, 92755),
            "Lap 3. Time 1 minute 32.472 seconds. "
            "Faster than your previous best by 0.283 seconds. New fastest lap.",
        )

    def test_slower_than_fastest_lap(self):
        self.assertEqual(
            sample_announcement(),
            "Lap 4. Time 1 minute 33.653 seconds. "
            "Slower than your fastest lap by 1.181 seconds.",
        )

    def test_matching_fastest_lap(self):
        self.assertEqual(
            format_lap_announcement(5, 92472, 92472),
            "Lap 5. Time 1 minute 32.472 seconds. Matching your fastest lap.",
        )

    def test_time_under_one_minute_omits_minutes(self):
        self.assertEqual(
            format_lap_announcement(2, 45100, None),
            "Lap 2. Time 45.100 seconds. First completed lap.",
        )


class TestCompletedLapSelection(unittest.TestCase):
    def test_ignores_replay_and_empty_laps_when_choosing_previous_best(self):
        completed = _lap(3, 92472)
        previous = [
            _lap(2, 80000, replay=True),
            _lap(1, 92755),
            _lap(0, 1000, speed=False),
        ]
        self.assertEqual(
            announcement_for_completed_lap(completed, previous),
            format_lap_announcement(3, 92472, 92755),
        )

    def test_replay_lap_is_not_announced(self):
        self.assertIsNone(announcement_for_completed_lap(_lap(1, 99214, replay=True), []))

    def test_lap_without_speed_data_is_not_announced(self):
        self.assertIsNone(announcement_for_completed_lap(_lap(1, 99214, speed=False), []))


class TestLapAnnouncer(unittest.TestCase):
    def test_speaks_once_and_does_not_change_stored_laps(self):
        completed = _lap(1, 99214)
        stored = [completed]
        announcer = LapAnnouncer(lambda: stored)

        with mock.patch("gt7dashboard.gt7voice.speak") as speak_mock:
            announcer.on_lap(completed)
            announcer.on_lap(completed)

        self.assertEqual(stored, [completed])
        speak_mock.assert_called_once_with(
            "Lap 1. Time 1 minute 39.214 seconds. First completed lap."
        )

    def test_compares_against_laps_stored_before_this_one(self):
        previous = _lap(1, 92472)
        completed = _lap(2, 93653)
        stored = [completed, previous]
        announcer = LapAnnouncer(lambda: stored)

        with mock.patch("gt7dashboard.gt7voice.speak") as speak_mock:
            announcer.on_lap(completed)

        speak_mock.assert_called_once_with(
            "Lap 2. Time 1 minute 33.653 seconds. "
            "Slower than your fastest lap by 1.181 seconds."
        )


class TestSpeak(unittest.TestCase):
    def test_sample_button_uses_speak(self):
        with mock.patch("gt7dashboard.gt7voice.speak") as speak_mock:
            play_sample_announcement()
        speak_mock.assert_called_once_with(sample_announcement())

    def test_speak_starts_say_without_waiting(self):
        with mock.patch("gt7dashboard.gt7voice.shutil.which", return_value="/usr/bin/say"), \
                mock.patch("gt7dashboard.gt7voice.subprocess.Popen") as popen, \
                mock.patch.dict("os.environ", {"GT7_LAP_ANNOUNCE": "true"}, clear=True):
            speak(sample_announcement())

        popen.assert_called_once_with(
            ["/usr/bin/say", "-v", "Daniel", sample_announcement()],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def test_speak_uses_daniel_when_voice_is_unset(self):
        with mock.patch("gt7dashboard.gt7voice.shutil.which", return_value="/usr/bin/say"), \
                mock.patch("gt7dashboard.gt7voice.subprocess.Popen") as popen, \
                mock.patch.dict("os.environ", {"GT7_LAP_ANNOUNCE": "true"}, clear=True):
            speak("Lap ready.")

        popen.assert_called_once_with(
            ["/usr/bin/say", "-v", "Daniel", "Lap ready."],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def test_speak_uses_voice_from_environment(self):
        with mock.patch("gt7dashboard.gt7voice.shutil.which", return_value="/usr/bin/say"), \
                mock.patch("gt7dashboard.gt7voice.subprocess.Popen") as popen, \
                mock.patch.dict(
                    "os.environ",
                    {"GT7_LAP_ANNOUNCE": "true", "GT7_LAP_VOICE": "Samantha"},
                    clear=True,
                ):
            speak("Lap ready.")

        popen.assert_called_once_with(
            ["/usr/bin/say", "-v", "Samantha", "Lap ready."],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def test_speak_does_nothing_when_disabled(self):
        with mock.patch("gt7dashboard.gt7voice.subprocess.Popen") as popen, \
                mock.patch.dict("os.environ", {"GT7_LAP_ANNOUNCE": "false"}):
            speak(sample_announcement())
        popen.assert_not_called()

    def test_speak_does_nothing_without_say(self):
        with mock.patch("gt7dashboard.gt7voice.shutil.which", return_value=None), \
                mock.patch("gt7dashboard.gt7voice.subprocess.Popen") as popen:
            speak(sample_announcement())
        popen.assert_not_called()
