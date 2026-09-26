import ast
import unittest
from pathlib import Path

from schemas.executions import ExecutionListItem, ExecutionListResponse


def active_execution_payload(**overrides):
    payload = {
        "id": 142,
        "source_type": "robot",
        "robot_id": 9,
        "robot_version": 3,
        "project_id": None,
        "robot_name": "Conciliação financeira",
        "filename": "conciliacao.zip",
        "folder_name": "Financeiro / Fechamento",
        "user_id": 1,
        "username": "operador",
        "user_name": "Operador DUET",
        "agent_id": "runner-03",
        "agent_name": "Financeiro 03",
        "schedule_id": None,
        "schedule_run_id": None,
        "pid": 4872,
        "status": "running",
        "started_at": "2026-09-26T14:45:00",
        "finished_at": None,
        "error_message": None,
    }
    payload.update(overrides)
    return payload


class ExecutionContractTests(unittest.TestCase):
    def test_active_execution_exposes_operational_context(self):
        item = ExecutionListItem.model_validate(active_execution_payload())
        response = ExecutionListResponse.model_validate({
            "status": "success",
            "total": 1,
            "executions": [item],
        })

        self.assertEqual(response.executions[0].robot_version, 3)
        self.assertEqual(response.executions[0].folder_name, "Financeiro / Fechamento")
        self.assertEqual(response.executions[0].pid, 4872)

    def test_development_execution_does_not_require_published_robot(self):
        item = ExecutionListItem.model_validate(active_execution_payload(
            source_type="development",
            robot_id=None,
            robot_version=None,
            project_id=27,
            schedule_id=8,
            schedule_run_id="schedule-8-20260926T144500",
            pid=None,
            status="queued",
            started_at=None,
        ))

        self.assertIsNone(item.robot_id)
        self.assertEqual(item.project_id, 27)
        self.assertEqual(item.status, "queued")

    def test_route_declares_typed_execution_response(self):
        source = Path("api/executions.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        list_route = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "list_executions"
        )
        response_model = next(
            keyword.value
            for decorator in list_route.decorator_list
            if isinstance(decorator, ast.Call)
            for keyword in decorator.keywords
            if keyword.arg == "response_model"
        )

        self.assertIsInstance(response_model, ast.Name)
        self.assertEqual(response_model.id, "ExecutionListResponse")


if __name__ == "__main__":
    unittest.main()
