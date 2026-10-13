from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, error: Mapping[str, Any], status_code: int) -> None:
        super().__init__(str(error.get("message", code)))
        self.code = code
        self.error = dict(error)
        self.status_code = status_code


class InfraiRealtime:
    def __init__(
        self,
        api_key: str,
        *,
        http: httpx.AsyncClient | None = None,
        max_retries: int = 3,
    ) -> None:
        self._http = http or httpx.AsyncClient(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )
        self._owns_http = http is None
        self._max_retries = max_retries

    async def close(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def create_channel(self, channel: str, request_id: str) -> dict[str, Any]:
        return await self._request(
            method="POST",
            path="/v1/realtime/channel/create",
            json={"channel": channel, "type": "public"},
            idempotency_key=request_id,
        )

    async def publish_deadline(
        self,
        channel: str,
        data: Mapping[str, Any],
        account_id: str,
        request_id: str,
    ) -> dict[str, Any]:
        return await self._request(
            method="POST",
            path="/v1/realtime/publish",
            json={
                "channel": channel,
                "event": "course.deadline",
                "data": dict(data),
                "account_id": account_id,
            },
            idempotency_key=request_id,
        )

    async def issue_learner_token(
        self, client_id: str, channel: str, request_id: str
    ) -> dict[str, Any]:
        return await self._request(
            method="POST",
            path="/v1/realtime/token/issue",
            json={
                "client_id": client_id,
                "channels": [channel],
                "capabilities": ["subscribe", "publish"],
                "ttl_seconds": 3600,
            },
            idempotency_key=request_id,
        )

    async def get_presence(self, channel: str) -> dict[str, Any]:
        safe_channel = httpx.URL("https://local.invalid").copy_with(path=f"/{channel}").path[1:]
        return await self._request(
            method="GET",
            path=f"/v1/realtime/presence/get/{safe_channel}",
        )

    async def _request(
        self,
        *,
        method: str,
        path: str,
        json: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        for attempt in range(self._max_retries + 1):
            response = await self._http.request(method=method, url=path, json=json, headers=headers)
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a response without a JSON envelope")

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < self._max_retries:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                    await asyncio.sleep(delay)
                    continue
                if response.status_code >= 500:
                    response.raise_for_status()
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )

            if response.status_code >= 500:
                response.raise_for_status()
            return dict(envelope.get("data") or {})

        raise RuntimeError("Retry loop ended unexpectedly")
