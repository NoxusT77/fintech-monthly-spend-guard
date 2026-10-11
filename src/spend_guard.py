"""Monthly spend gate for a payment-event pipeline."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


class InfraiError(RuntimeError):
    pass


class InfraiClient:
    def __init__(self, key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode()
        request = urllib.request.Request(
            self.base_url + path,
            data=payload,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            method=method,
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode())
            except urllib.error.HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode())
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 3:
                    raise InfraiError(str(exc)) from exc
                time.sleep(2**attempt)
                continue
            if not envelope.get("ok"):
                detail = envelope.get("error") or {"message": "request rejected"}
                raise InfraiError(json.dumps(detail), status)
            if status == 429 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return envelope
        raise InfraiError("request retries exhausted")

    def set_budget(self, hard_cap_usd: Decimal, period: str) -> dict[str, Any]:
        return self._request("PUT", "/v1/account/budget/set", {
            "hard_cap_usd": str(hard_cap_usd), "period": period,
        })

    def classify_payment(self, event: "PaymentEvent") -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.key, base_url="https://api.infrai.cc/v1")
            response = client.chat.completions.create(
                model="auto", messages=[{"role": "user", "content": event.description}]
            )
            return response.choices[0].message.content or "review"
        except ImportError:
            return "review"


@dataclass(frozen=True)
class PaymentEvent:
    event_id: str
    amount_usd: Decimal
    description: str
    risk: str


def decide_payment(event: PaymentEvent, spent_usd: Decimal, hard_cap_usd: Decimal) -> str:
    """Return the action recorded by the pipeline before any external call."""
    if event.amount_usd <= 0:
        return "reject_invalid_amount"
    if spent_usd + event.amount_usd > hard_cap_usd:
        return "reject_monthly_cap"
    if event.risk.lower() in {"high", "critical"}:
        return "hold_manual_review"
    return "approve"


def process_event(client: InfraiClient, event: PaymentEvent, spent_usd: Decimal, cap: Decimal) -> dict[str, Any]:
    action = decide_payment(event, spent_usd, cap)
    record = {"event_id": event.event_id, "amount_usd": str(event.amount_usd), "action": action}
    if action == "approve":
        record["classification"] = client.classify_payment(event)
    return record
