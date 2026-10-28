"""Invoice fields and the rules that decide `accepted` or `needs_review`."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

# Tax is often rounded per line, so totals can drift by a cent or two.
ROUNDING_TOLERANCE = Decimal("0.02")


class InvoiceFields(BaseModel):
    # Optional, so a missing field is flagged for review instead of crashing.
    # Decimal, not float, so money adds up exactly.
    supplier_name: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    subtotal: Decimal | None = None
    tax: Decimal | None = None
    total: Decimal | None = None
    currency: str | None = None


def validate(fields: InvoiceFields) -> dict:
    reasons = [
        f"Missing {name}"
        for name, value in fields
        if value is None or str(value).strip() == ""
    ]

    if None not in (fields.subtotal, fields.tax, fields.total):
        difference = abs(fields.subtotal + fields.tax - fields.total)
        if difference > ROUNDING_TOLERANCE:
            reasons.append(f"subtotal + tax does not equal total (off by {difference})")

    return {"status": "needs_review" if reasons else "accepted", "reasons": reasons}
