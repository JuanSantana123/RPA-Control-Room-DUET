import unittest
import ast
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from robots.serializers import serialize_robot_version_catalog_item


class RobotVersionSerializerTests(unittest.TestCase):
    def setUp(self):
        self.version = SimpleNamespace(
            id=17,
            version=4,
            filename="financeiro-v4.zip",
            file_hash="a" * 64,
            published_at=datetime(2026, 9, 26, 18, 30),
            created_at=datetime(2026, 9, 26, 18, 31),
            artifact_path="storage/releases/segredo.zip",
        )

    def test_serializes_release_provenance_and_current_state(self):
        result = serialize_robot_version_catalog_item(
            self.version,
            current_version=4,
            publisher=SimpleNamespace(id=3, name="Maria Souza", username="maria"),
            source_project=SimpleNamespace(id=22, name="Conciliação 2026"),
        )

        self.assertTrue(result["is_current"])
        self.assertEqual(result["publisher"]["name"], "Maria Souza")
        self.assertEqual(result["source_project"]["id"], 22)
        self.assertEqual(result["published_at"], "2026-09-26T18:30:00")

    def test_does_not_expose_server_artifact_path(self):
        result = serialize_robot_version_catalog_item(
            self.version,
            current_version=5,
            publisher=None,
            source_project=None,
        )

        self.assertFalse(result["is_current"])
        self.assertIsNone(result["publisher"])
        self.assertIsNone(result["source_project"])
        self.assertNotIn("artifact_path", result)

    def test_catalog_route_declares_typed_response(self):
        source = (Path(__file__).parents[1] / "api" / "robots.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        route = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "list_robot_versions"
        )
        decorator = next(
            item
            for item in route.decorator_list
            if isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr == "get"
        )
        response_model = next(
            keyword.value
            for keyword in decorator.keywords
            if keyword.arg == "response_model"
        )
        self.assertIsInstance(response_model, ast.Name)
        self.assertEqual(response_model.id, "RobotVersionsResponse")


if __name__ == "__main__":
    unittest.main()
