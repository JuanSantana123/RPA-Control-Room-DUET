import os
import unittest
from datetime import datetime
from unittest.mock import patch

from core.timezone import (
    get_control_room_timezone_name,
    local_now_naive,
    validate_local_wall_time,
)


class ControlRoomTimezoneTests(unittest.TestCase):
    def test_default_timezone_is_explicit_and_clock_remains_database_compatible(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_control_room_timezone_name(), "America/Sao_Paulo")
            self.assertIsNone(local_now_naive().tzinfo)

    def test_nonexistent_dst_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "não existe"):
            validate_local_wall_time(
                datetime(2026, 3, 8, 2, 30),
                "America/New_York",
            )

    def test_ambiguous_dst_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "ambíguo"):
            validate_local_wall_time(
                datetime(2026, 11, 1, 1, 30),
                "America/New_York",
            )

    def test_regular_wall_time_is_accepted(self):
        validate_local_wall_time(
            datetime(2026, 9, 26, 8, 0),
            "America/Sao_Paulo",
        )


if __name__ == "__main__":
    unittest.main()
