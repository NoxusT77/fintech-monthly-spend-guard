import json
import os
from decimal import Decimal

from src.spend_guard import InfraiClient, PaymentEvent, process_event


def main() -> None:
    client = InfraiClient()
    cap = Decimal(os.environ.get("MONTHLY_HARD_CAP_USD", "1000"))
    period = os.environ.get("BUDGET_PERIOD", "monthly")
    client.set_budget(cap, period)
    event = PaymentEvent("evt_demo_001", Decimal("125.00"), "settle card payment", "low")
    print(json.dumps(process_event(client, event, Decimal("640.00"), cap)))


if __name__ == "__main__":
    main()

