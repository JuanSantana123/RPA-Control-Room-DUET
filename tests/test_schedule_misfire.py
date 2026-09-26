import os
import unittest
from datetime import datetime
from types import SimpleNamespace


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://duet_test:duet_test@127.0.0.1:1/duet_test",
)

from scheduler.execution import aplicar_politica_de_ocorrencia_perdida
from schemas.schedules import ScheduleCreateRequest, ScheduleListResponse


def schedule_stub(**overrides):
    values = {
        "tipo": "daily",
        "data_inicio": datetime(2026, 9, 1),
        "horario": "08:00",
        "dias_semana": None,
        "intervalo_ativo": 0,
        "intervalo_valor": None,
        "intervalo_unidade": None,
        "horario_fim": None,
        "ativo": 1,
        "proxima_execucao": datetime(2026, 9, 26, 8, 0),
        "misfire_policy": "skip",
        "misfire_grace_seconds": 300,
        "ultima_ocorrencia_perdida": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class ScheduleMisfireTests(unittest.TestCase):
    def test_run_once_preserves_backward_compatible_recovery(self):
        schedule = schedule_stub(misfire_policy="run_once")

        skipped = aplicar_politica_de_ocorrencia_perdida(
            schedule,
            datetime(2026, 9, 26, 10, 0),
        )

        self.assertFalse(skipped)
        self.assertEqual(schedule.proxima_execucao, datetime(2026, 9, 26, 8, 0))

    def test_skip_policy_respects_grace_window(self):
        schedule = schedule_stub(misfire_grace_seconds=300)

        skipped = aplicar_politica_de_ocorrencia_perdida(
            schedule,
            datetime(2026, 9, 26, 8, 4, 59),
        )

        self.assertFalse(skipped)
        self.assertIsNone(schedule.ultima_ocorrencia_perdida)

    def test_recurring_schedule_records_misfire_and_advances(self):
        schedule = schedule_stub()

        skipped = aplicar_politica_de_ocorrencia_perdida(
            schedule,
            datetime(2026, 9, 26, 10, 0),
        )

        self.assertTrue(skipped)
        self.assertEqual(schedule.ultima_ocorrencia_perdida, datetime(2026, 9, 26, 8, 0))
        self.assertEqual(schedule.proxima_execucao, datetime(2026, 9, 27, 8, 0))
        self.assertEqual(schedule.ativo, 1)

    def test_once_schedule_is_preserved_inactive_after_misfire(self):
        schedule = schedule_stub(tipo="once")

        skipped = aplicar_politica_de_ocorrencia_perdida(
            schedule,
            datetime(2026, 9, 26, 10, 0),
        )

        self.assertTrue(skipped)
        self.assertEqual(schedule.ativo, 0)
        self.assertIsNone(schedule.proxima_execucao)

    def test_contract_rejects_unsafe_grace_or_unknown_policy(self):
        base = {
            "robot_id": 1,
            "tipo": "daily",
            "data_inicio": "2026-09-27T08:00:00",
            "horario": "08:00",
        }

        with self.assertRaises(ValueError):
            ScheduleCreateRequest.model_validate({**base, "misfire_grace_seconds": 5})

        with self.assertRaises(ValueError):
            ScheduleCreateRequest.model_validate({**base, "misfire_policy": "replay_all"})

    def test_list_contract_exposes_recovery_evidence(self):
        response = ScheduleListResponse.model_validate({
            "status": "success",
            "total": 1,
            "schedules": [{
                "id": 18,
                "robot_id": 12,
                "robot_name": "Conciliação financeira",
                "agent_id": None,
                "agent_name": "Automático",
                "tipo": "daily",
                "data_inicio": "2026-09-20T08:00:00",
                "horario": "08:00",
                "dias_semana": None,
                "ativo": True,
                "proxima_execucao": "2026-09-27T08:00:00",
                "ultima_execucao": "2026-09-25T08:00:05",
                "intervalo_ativo": False,
                "intervalo_valor": None,
                "intervalo_unidade": None,
                "horario_fim": None,
                "misfire_policy": "skip",
                "misfire_grace_seconds": 600,
                "ultima_ocorrencia_perdida": "2026-09-26T08:00:00",
            }],
        })

        self.assertEqual(response.schedules[0].misfire_policy, "skip")
        self.assertEqual(response.schedules[0].ultima_ocorrencia_perdida, "2026-09-26T08:00:00")


if __name__ == "__main__":
    unittest.main()
