import os
import unittest
from datetime import datetime
from unittest.mock import patch

from pydantic import ValidationError

from core.queue_policy import (
    DEFAULT_QUEUE_WARNING_SECONDS,
    get_queue_warning_seconds,
    queue_sort_key,
)
from schemas.executions import ExecutionPriorityUpdateRequest


class QueuePolicyTests(unittest.TestCase):
    def test_priority_precedes_fifo_and_id_tiebreaker(self):
        queued_at = datetime(2026, 9, 26, 10, 0, 0)
        ordered = sorted(
            [
                ("normal", queued_at, 8),
                ("urgent", queued_at, 9),
                ("normal", queued_at, 7),
                ("high", queued_at, 6),
            ],
            key=lambda item: queue_sort_key(*item),
        )

        self.assertEqual(
            ordered,
            [
                ("urgent", queued_at, 9),
                ("high", queued_at, 6),
                ("normal", queued_at, 7),
                ("normal", queued_at, 8),
            ],
        )

    def test_wait_threshold_is_bounded_and_has_safe_default(self):
        for raw_value in ("", "invalid", "59", "86401"):
            with self.subTest(raw_value=raw_value), patch.dict(
                os.environ,
                {"DUET_QUEUE_WARNING_SECONDS": raw_value},
                clear=False,
            ):
                self.assertEqual(get_queue_warning_seconds(), DEFAULT_QUEUE_WARNING_SECONDS)

        with patch.dict(os.environ, {"DUET_QUEUE_WARNING_SECONDS": "1800"}, clear=False):
            self.assertEqual(get_queue_warning_seconds(), 1800)

    def test_priority_contract_rejects_unknown_values(self):
        with self.assertRaises(ValidationError):
            ExecutionPriorityUpdateRequest(priority="critical")


if __name__ == "__main__":
    unittest.main()
