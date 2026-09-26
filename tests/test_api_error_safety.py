import ast
import unittest
from pathlib import Path


API_DIRECTORY = Path(__file__).resolve().parents[1] / "api"


def _is_raw_exception_text(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "str"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id in {"error", "exception", "exc"}
    )


def _is_raw_response_body(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr in {"text", "content"}
        and isinstance(node.value, ast.Name)
        and node.value.id in {"response", "resposta"}
    )


class ApiErrorSafetyTests(unittest.TestCase):
    def test_http_responses_do_not_expose_raw_exception_or_upstream_body(self):
        violations: list[str] = []

        for file_path in sorted(API_DIRECTORY.glob("*.py")):
            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))

            for node in ast.walk(tree):
                if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Dict):
                    continue

                for value in node.value.values:
                    if value is None:
                        continue
                    if _is_raw_exception_text(value) or _is_raw_response_body(value):
                        violations.append(f"{file_path.name}:{node.lineno}")

        self.assertEqual(
            violations,
            [],
            "Respostas HTTP expõem detalhes técnicos brutos em: " + ", ".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
