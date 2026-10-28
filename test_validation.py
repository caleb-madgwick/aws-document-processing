import pytest
from pydantic import ValidationError

from validation import InvoiceFields, validate

GOOD_INVOICE = {
    "supplier_name": "Northwind Office Supplies",
    "invoice_number": "INV-1001",
    "invoice_date": "2026-09-15",
    "subtotal": "100.00",
    "tax": "10.00",
    "total": "110.00",
    "currency": "AUD",
}


def invoice(**changes):
    return InvoiceFields(**{**GOOD_INVOICE, **changes})


def test_complete_invoice_is_accepted():
    assert validate(invoice()) == {"status": "accepted", "reasons": []}


def test_missing_and_blank_fields_need_review():
    result = validate(invoice(invoice_number=None, supplier_name="  "))

    assert result["status"] == "needs_review"
    assert result["reasons"] == ["Missing supplier_name", "Missing invoice_number"]


@pytest.mark.parametrize(
    "total, status",
    [("110.02", "accepted"), ("110.03", "needs_review"), ("120.00", "needs_review")],
)
def test_subtotal_plus_tax_must_equal_total_within_rounding(total, status):
    assert validate(invoice(total=total))["status"] == status


def test_unreadable_date_is_rejected_by_pydantic():
    with pytest.raises(ValidationError):
        invoice(invoice_date="not a date")
