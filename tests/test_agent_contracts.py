import unittest
from datetime import datetime
from types import SimpleNamespace

from pydantic import ValidationError

from agents.serializers import (
    serializar_agent_consulta,
    serializar_agent_execucao,
    serializar_agent_lista,
)
from schemas.agents import (
    AgentAvailabilityUpdateRequest,
    AgentCatalogItem,
    AgentDetailSuccessResponse,
    AgentExecutionItem,
    AgentListResponse,
)


def criar_agent_teste(**overrides):
    dados = {
        "agent_id": "AGENT-TESTE",
        "name": "Device de homologação",
        "environment": "development",
        "host": None,
        "port": 8000,
        "rpa_directory": "C:\\RPA-Agent",
        "status": "online",
        "accepting_work": True,
        "maintenance_reason": None,
        "availability_updated_at": None,
        "last_heartbeat": datetime(2026, 9, 26, 10, 30),
        "session_status": "ready",
        "username": "sessao.atual",
        "execution_username": "duet_rpa",
        "execution_domain": "RPA",
        "display_width": 1920,
        "display_height": 1080,
        "display_scale": 100,
        "display_current_width": 1920,
        "display_current_height": 1080,
        "display_supported": [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
        ],
    }
    dados.update(overrides)
    return SimpleNamespace(**dados)


class AgentContractTests(unittest.TestCase):
    def test_listagem_inclui_status_e_valida_contrato_publico(self):
        payload = serializar_agent_lista(criar_agent_teste())

        item = AgentCatalogItem.model_validate(payload)
        resposta = AgentListResponse.model_validate({
            "status": "success",
            "total": 1,
            "agents": [payload],
        })

        self.assertEqual(item.status, "online")
        self.assertEqual(resposta.agents[0].session_status, "ready")

    def test_consulta_entrega_estado_da_sessao_sem_expor_token(self):
        payload = serializar_agent_consulta(criar_agent_teste())
        resposta = AgentDetailSuccessResponse.model_validate({
            "status": "success",
            "agent": payload,
        })

        self.assertEqual(resposta.agent.username, "sessao.atual")
        self.assertNotIn("agent_token", payload)
        self.assertNotIn("agent_token_hash", payload)
        self.assertNotIn("agent_token_encrypted", payload)

    def test_seletor_de_execucao_valida_contrato_minimo(self):
        payload = serializar_agent_execucao(criar_agent_teste())

        item = AgentExecutionItem.model_validate(payload)

        self.assertEqual(item.agent_id, "AGENT-TESTE")
        self.assertEqual(item.environment, "development")

    def test_telemetria_de_display_invalida_e_descartada(self):
        payload = serializar_agent_lista(criar_agent_teste(
            display_supported=[
                {"width": 1920, "height": 1080},
                {"width": 0, "height": 1080},
                {"width": True, "height": 720},
                {"width": "1366", "height": 768},
                "invalido",
            ],
        ))

        self.assertEqual(
            payload["display_supported"],
            [{"width": 1920, "height": 1080}],
        )

    def test_manutencao_exige_motivo_e_normaliza_espacos(self):
        with self.assertRaises(ValidationError):
            AgentAvailabilityUpdateRequest(
                accepting_work=False,
                reason="   ",
            )

        request = AgentAvailabilityUpdateRequest(
            accepting_work=False,
            reason="  Atualização programada do Windows  ",
        )

        self.assertEqual(request.reason, "Atualização programada do Windows")

    def test_liberacao_remove_motivo_anterior(self):
        request = AgentAvailabilityUpdateRequest(
            accepting_work=True,
            reason="Motivo antigo",
        )

        self.assertIsNone(request.reason)

    def test_serializers_expoem_disponibilidade_sem_segredos(self):
        agent = criar_agent_teste(
            accepting_work=False,
            maintenance_reason="Atualização programada",
            availability_updated_at=datetime(2026, 9, 26, 11, 0),
        )

        administrative = serializar_agent_lista(agent)
        execution = serializar_agent_execucao(agent)

        self.assertFalse(administrative["accepting_work"])
        self.assertEqual(execution["maintenance_reason"], "Atualização programada")
        self.assertNotIn("agent_token", administrative)
        self.assertNotIn("agent_token", execution)


if __name__ == "__main__":
    unittest.main()
