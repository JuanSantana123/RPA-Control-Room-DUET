import unittest
import uuid

from core.http_middleware import RequestContextMiddleware
from core.request_context import get_request_id


class RequestContextMiddlewareTests(unittest.IsolatedAsyncioTestCase):
    async def _request(self, request_id=None):
        observed_context = []

        async def app(scope, receive, send):
            observed_context.append(get_request_id())
            await send({
                "type": "http.response.start",
                "status": 204,
                "headers": [],
            })
            await send({"type": "http.response.body", "body": b""})

        sent = []

        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(message):
            sent.append(message)

        headers = []
        if request_id:
            headers.append((b"x-client-request-id", request_id.encode("ascii")))

        await RequestContextMiddleware(app)(
            {
                "type": "http",
                "method": "GET",
                "path": "/health/live",
                "headers": headers,
            },
            receive,
            send,
        )
        response_headers = dict(sent[0]["headers"])
        return observed_context[0], response_headers

    async def test_valid_client_request_id_is_preserved(self):
        request_id = "client-request-1234"
        observed, headers = await self._request(request_id)

        self.assertEqual(observed, request_id)
        self.assertEqual(headers[b"x-request-id"], request_id.encode("ascii"))
        self.assertEqual(headers[b"x-content-type-options"], b"nosniff")
        self.assertEqual(headers[b"x-frame-options"], b"DENY")
        self.assertIsNone(get_request_id())

    async def test_invalid_client_request_id_is_replaced(self):
        observed, headers = await self._request("invalid header with spaces")

        generated = headers[b"x-request-id"].decode("ascii")
        self.assertEqual(observed, generated)
        self.assertEqual(str(uuid.UUID(generated)), generated)


if __name__ == "__main__":
    unittest.main()
