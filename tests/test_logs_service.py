import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from logs.service import listar_logs_service
from schemas.logs import LogsSuccessResponse


class LogsServiceTests(unittest.TestCase):
    def test_limite_e_aplicado_depois_do_filtro_e_metadados_sao_sanitizados(self):
        registros = [
            {"timestamp": "1", "level": "ERROR", "message": "primeiro", "exception": "segredo"},
            {"timestamp": "2", "level": "INFO", "message": "intermediario"},
            {"timestamp": "3", "level": "ERROR", "message": "segundo", "request_id": "req-3"},
            {"timestamp": "4", "level": "ERROR", "message": "terceiro", "event": "falha_teste"},
        ]

        with tempfile.TemporaryDirectory() as diretorio:
            arquivo = Path(diretorio) / "control_room.log"
            arquivo.write_text(
                "\n".join(json.dumps(registro) for registro in registros),
                encoding="utf-8",
            )

            with patch("logs.service.LOG_FILE", arquivo):
                resposta = listar_logs_service(limit=2, level="ERROR")

        contrato = LogsSuccessResponse.model_validate(resposta)
        self.assertEqual(contrato.total, 3)
        self.assertTrue(contrato.truncated)
        self.assertEqual([item.message for item in contrato.logs], ["terceiro", "segundo"])
        self.assertNotIn("exception", resposta["logs"][0])

    def test_linhas_invalidas_nao_interrompem_a_consulta(self):
        with tempfile.TemporaryDirectory() as diretorio:
            arquivo = Path(diretorio) / "control_room.log"
            arquivo.write_text(
                "invalido\n[]\n" + json.dumps({"level": "INFO", "message": "ok"}),
                encoding="utf-8",
            )

            with patch("logs.service.LOG_FILE", arquivo):
                resposta = listar_logs_service(limit=10)

        self.assertEqual(resposta["total"], 1)
        self.assertEqual(resposta["logs"][0]["message"], "ok")


if __name__ == "__main__":
    unittest.main()
