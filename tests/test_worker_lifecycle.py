import os
import unittest
from unittest.mock import patch


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://duet_test:duet_test@127.0.0.1:1/duet_test",
)

from agents import monitoring_service  # noqa: E402
from executions import queue  # noqa: E402
from scheduler import engine  # noqa: E402


class WorkerLifecycleTests(unittest.TestCase):
    def tearDown(self):
        monitoring_service.parar_monitor_agents(timeout_seconds=1)
        queue.parar_worker_fila(timeout_seconds=1)
        engine.parar_scheduler(timeout_seconds=1)

    def test_scheduler_starts_once_and_stops(self):
        with patch.object(engine, "processar_ciclo_scheduler", return_value=None):
            engine.iniciar_scheduler()
            first_thread = engine.scheduler_thread
            engine.iniciar_scheduler()

            self.assertIsNotNone(first_thread)
            self.assertIs(engine.scheduler_thread, first_thread)
            self.assertTrue(first_thread.is_alive())

            engine.parar_scheduler(timeout_seconds=1)
            self.assertIsNone(engine.scheduler_thread)

    def test_execution_queue_starts_once_and_stops(self):
        with patch.object(queue, "processar_ciclo_fila", return_value=0):
            queue.iniciar_worker_fila()
            first_thread = queue.thread_fila
            queue.iniciar_worker_fila()

            self.assertIsNotNone(first_thread)
            self.assertIs(queue.thread_fila, first_thread)
            self.assertTrue(first_thread.is_alive())

            queue.parar_worker_fila(timeout_seconds=1)
            self.assertIsNone(queue.thread_fila)

    def test_agent_monitor_starts_once_and_stops(self):
        with patch.object(
            monitoring_service,
            "verificar_agents_offline",
            return_value=None,
        ):
            monitoring_service.iniciar_monitor_agents()
            first_thread = monitoring_service.agent_monitor_thread
            monitoring_service.iniciar_monitor_agents()

            self.assertIsNotNone(first_thread)
            self.assertIs(monitoring_service.agent_monitor_thread, first_thread)
            self.assertTrue(first_thread.is_alive())

            monitoring_service.parar_monitor_agents(timeout_seconds=1)
            self.assertIsNone(monitoring_service.agent_monitor_thread)


if __name__ == "__main__":
    unittest.main()
