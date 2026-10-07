import logging
import time

from core.request_context import normalize_request_id, request_id_context


logger = logging.getLogger("control_room")


class RequestContextMiddleware:
    """Adiciona correlação, telemetria HTTP e headers defensivos."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        request_id = normalize_request_id(headers.get("x-client-request-id"))
        token = request_id_context.set(request_id)
        started_at = time.perf_counter()
        status_code = 500

        async def send_with_headers(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = list(message.get("headers", []))
                response_headers.extend([
                    (b"x-request-id", request_id.encode("ascii")),
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                ])
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        except Exception:
            logger.exception(
                "Falha não tratada durante requisição HTTP",
                extra={
                    "event": "http_request_failed",
                    "category": "SYSTEM",
                    "component": "http",
                    "ui_visible": True,
                    "http_method": scope.get("method"),
                    "endpoint": scope.get("path"),
                    "http_status": 500,
                    "request_id": request_id,
                },
            )
            raise
        finally:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.info(
                "Requisição HTTP concluída",
                extra={
                    "event": "http_request_completed",
                    "category": "HTTP",
                    "component": "http",
                    "ui_visible": False,
                    "http_method": scope.get("method"),
                    "endpoint": scope.get("path"),
                    "http_status": status_code,
                    "duration_ms": duration_ms,
                    "request_id": request_id,
                },
            )
            request_id_context.reset(token)
