from __future__ import annotations

from typing import Any

import threading

import requests


class DuetApiError(RuntimeError):
    """Erro HTTP normalizado do Control Room."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _response_message(response: requests.Response) -> str:
    try:
        payload = response.json()
        detail = payload.get("detail")

        if isinstance(detail, str):
            return detail

        if isinstance(detail, dict):
            message = detail.get("message")
            if isinstance(message, str):
                return message

        message = payload.get("message")
        if isinstance(message, str):
            return message
    except Exception:
        pass

    return f"Control Room respondeu HTTP {response.status_code}."


class DuetApiClient:
    """Cliente HTTP exclusivo do Developer Bridge."""

    def __init__(self, server: str):
        self.server = server.rstrip("/")
        self.http = requests.Session()
        self.access_token: str | None = None

        # requests.Session não deve ser utilizada concorrentemente sem
        # coordenação. O Bridge possui watcher, timers e loop de renovação.
        self._request_lock = threading.RLock()

    def _url(self, path: str) -> str:
        return f"{self.server}{path}"

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}

        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    def _request(self, method: str, path: str, **kwargs) -> Any:
        """
        Executa uma chamada autenticada de forma serializada.

        Erros de transporte também são normalizados como DuetApiError
        para que a camada de sincronização consiga manter a alteração
        local pendente em vez de perdê-la.
        """

        with self._request_lock:
            try:
                response = self.http.request(
                    method=method,
                    url=self._url(path),
                    headers=self._headers(),
                    timeout=30,
                    **kwargs,
                )
            except requests.RequestException as error:
                raise DuetApiError(
                    (
                        "Não foi possível comunicar com o "
                        "DUET Control Room."
                    ),
                    None,
                ) from error

            if not response.ok:
                raise DuetApiError(
                    _response_message(response),
                    response.status_code,
                )

            if not response.content:
                return None

            return response.json()

    def redeem(self, launch_code: str) -> dict:
        payload = self._request(
            "POST",
            "/development/external-ide/redeem",
            json={"launch_code": launch_code},
        )
        self.access_token = payload["access_token"]
        return payload

    def get_tree(self) -> list[dict]:
        payload = self._request(
            "GET",
            "/development/external-ide/workspace/tree",
        )
        return payload.get("tree") or []

    def get_file(self, path: str) -> str:
        payload = self._request(
            "GET",
            "/development/external-ide/workspace/file",
            params={"path": path},
        )
        return payload.get("content") or ""

    def save_file(self, path: str, content: str) -> None:
        self._request(
            "PUT",
            "/development/external-ide/workspace/file",
            json={"path": path, "content": content},
        )

    def create_file(self, path: str) -> None:
        self._request(
            "POST",
            "/development/external-ide/workspace/files",
            json={"path": path},
        )

    def create_folder(self, path: str) -> None:
        self._request(
            "POST",
            "/development/external-ide/workspace/folders",
            json={"path": path},
        )

    def rename_item(self, path: str, new_name: str) -> None:
        self._request(
            "PATCH",
            "/development/external-ide/workspace/item",
            json={"path": path, "new_name": new_name},
        )

    def delete_item(self, path: str, recursive: bool = True) -> None:
        self._request(
            "DELETE",
            "/development/external-ide/workspace/item",
            params={"path": path, "recursive": str(recursive).lower()},
        )

    def validate_session(self) -> dict:
        return self._request(
            "GET",
            "/development/external-ide/session",
        )

    def renew_session(self) -> dict:
        """
        Prolonga a sessão atual do Developer Bridge.

        O backend revalida usuário, permissões e Checkout antes de
        estender expires_at.
        """

        return self._request(
            "POST",
            "/development/external-ide/session/renew",
        )

    def revoke(self) -> None:
        if not self.access_token:
            return

        try:
            self._request(
                "DELETE",
                "/development/external-ide/session",
            )
        finally:
            self.access_token = None
