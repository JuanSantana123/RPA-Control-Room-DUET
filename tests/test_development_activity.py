from datetime import datetime
import os
from types import SimpleNamespace
import unittest

from pydantic import ValidationError

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://duet_test:duet_test@127.0.0.1:1/duet_test",
)

from development.comment_attachments_service import _detectar_imagem, _estrutura_imagem_valida
from development.serializers import serializar_comentario
from schemas.development import ProjectActivityListResponse, ProjectCommentCreate


class DevelopmentActivityContractTests(unittest.TestCase):
    def test_comment_payload_limits_attachments(self):
        payload = ProjectCommentCreate(content="Revisão concluída", attachment_ids=[1, 2])
        self.assertEqual(payload.attachment_ids, [1, 2])

        with self.assertRaises(ValidationError):
            ProjectCommentCreate(content="Muitas imagens", attachment_ids=[1, 2, 3, 4, 5, 6])

    def test_activity_contract_distinguishes_comments_and_movements(self):
        response = ProjectActivityListResponse.model_validate({
            "status": "success",
            "project_id": 7,
            "total": 2,
            "comments": [
                {
                    "id": 3,
                    "event_key": "comment-3",
                    "kind": "comment",
                    "project_id": 7,
                    "user_id": 1,
                    "user_name": "Operador",
                    "content": "Pronto para revisão.",
                    "attachments": [],
                    "created_at": "2026-09-27T10:00:00",
                    "updated_at": "2026-09-27T10:00:00",
                },
                {
                    "id": 9,
                    "event_key": "stage-movement-9",
                    "kind": "stage_movement",
                    "project_id": 7,
                    "user_id": 1,
                    "user_name": "Operador",
                    "content": None,
                    "attachments": [],
                    "from_stage": {"id": 1, "code": "BACKLOG", "name": "Backlog"},
                    "to_stage": {"id": 2, "code": "IN_PROGRESS", "name": "Em desenvolvimento"},
                    "created_at": "2026-09-27T10:02:00",
                    "updated_at": "2026-09-27T10:02:00",
                },
            ],
        })
        self.assertEqual(response.comments[1].kind, "stage_movement")
        self.assertEqual(response.comments[1].to_stage.name, "Em desenvolvimento")

    def test_attachment_serializer_does_not_expose_storage_key(self):
        timestamp = datetime(2026, 9, 27, 10, 0)
        comment = SimpleNamespace(
            id=4,
            project_id=7,
            user_id=1,
            content="Evidência anexada.",
            created_at=timestamp,
            updated_at=timestamp,
        )
        attachment = SimpleNamespace(
            id=6,
            project_id=7,
            comment_id=4,
            original_name="evidencia.png",
            media_type="image/png",
            size_bytes=128,
            storage_key="7/segredo.png",
            created_at=timestamp,
        )
        serialized = serializar_comentario(comment, "Operador", [attachment])
        self.assertEqual(serialized["kind"], "comment")
        self.assertNotIn("storage_key", serialized["attachments"][0])

    def test_image_type_is_detected_from_signature(self):
        self.assertEqual(_detectar_imagem(b"\x89PNG\r\n\x1a\nresto"), ("image/png", "png"))
        self.assertIsNone(_detectar_imagem(b"arquivo-nao-imagem"))
        self.assertFalse(_estrutura_imagem_valida("image/png", b"\x89PNG\r\n\x1a\nDUET", b"DUET", 12))


if __name__ == "__main__":
    unittest.main()
