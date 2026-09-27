import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from core.agent_health import (
    DEFAULT_AGENT_HEARTBEAT_TIMEOUT_SECONDS,
    describe_agent_health,
    get_agent_heartbeat_timeout_seconds,
)


class AgentHealthTests(unittest.TestCase):
    def test_health_distinguishes_never_seen_stale_and_offline(self):
        now = datetime(2026, 9, 26, 15, 0)

        self.assertEqual(
            describe_agent_health("pending", None, now=now),
            ("never_seen", None),
        )
        self.assertEqual(
            describe_agent_health(
                "online",
                now - timedelta(seconds=61),
                now=now,
                timeout_seconds=60,
            ),
            ("stale", 61),
        )
        self.assertEqual(
            describe_agent_health(
                "offline",
                now - timedelta(seconds=20),
                now=now,
                timeout_seconds=60,
            ),
            ("offline", 20),
        )

    def test_future_heartbeat_age_is_clamped(self):
        now = datetime(2026, 9, 26, 15, 0)
        self.assertEqual(
            describe_agent_health(
                "online",
                now + timedelta(seconds=5),
                now=now,
            ),
            ("healthy", 0),
        )

    def test_timeout_configuration_is_bounded(self):
        for raw_value in ("", "invalid", "14", "3601"):
            with self.subTest(raw_value=raw_value), patch.dict(
                os.environ,
                {"DUET_AGENT_HEARTBEAT_TIMEOUT_SECONDS": raw_value},
                clear=False,
            ):
                self.assertEqual(
                    get_agent_heartbeat_timeout_seconds(),
                    DEFAULT_AGENT_HEARTBEAT_TIMEOUT_SECONDS,
                )

        with patch.dict(
            os.environ,
            {"DUET_AGENT_HEARTBEAT_TIMEOUT_SECONDS": "120"},
            clear=False,
        ):
            self.assertEqual(get_agent_heartbeat_timeout_seconds(), 120)


if __name__ == "__main__":
    unittest.main()
