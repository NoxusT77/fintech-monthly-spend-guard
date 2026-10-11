import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.spend_guard import PaymentEvent, decide_payment


def test_cap_rejects_event_before_spend_call():
    event = PaymentEvent("evt_7", Decimal("40"), "wire transfer", "low")
    assert decide_payment(event, Decimal("980"), Decimal("1000")) == "reject_monthly_cap"


def test_high_risk_is_held_when_under_cap():
    event = PaymentEvent("evt_8", Decimal("40"), "cash withdrawal", "high")
    assert decide_payment(event, Decimal("900"), Decimal("1000")) == "hold_manual_review"
