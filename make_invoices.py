"""Generate fictional supplier invoices as one-page PDFs, plus the values printed on each.

Run: python make_invoices.py
Writes invoices/*.pdf and invoices/expected.json (the answer key).
"""

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from itertools import zip_longest
from pathlib import Path

from fpdf import FPDF

from validation import InvoiceFields, validate

OUT_DIR = Path("invoices")
CENT = Decimal("0.01")
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


@dataclass
class Invoice:
    file: str
    layout: str  # a key of LAYOUTS
    scenario: str
    supplier: str
    address: str
    tax_id: str  # ABN or GST number: a distractor next to the invoice number
    customer: str
    number: str | None  # None = not printed
    issued: date
    date_format: str
    currency: str | None  # None = not printed
    lines: list[tuple[str, int, str]]  # (description, quantity, unit price)
    colour: tuple[int, int, int] = BLACK
    font: str = "Helvetica"  # Helvetica, Times or Courier
    due_days: int | None = None  # a due date is a distractor next to the invoice date
    tax_rate: Decimal = Decimal("0.10")
    prices_include_tax: bool = False  # receipts show GST-inclusive prices
    total_error: str = "0"  # added to the printed total to simulate a mistake

    @property
    def line_sum(self) -> Decimal:
        return sum(qty * Decimal(price) for _, qty, price in self.lines)

    @property
    def tax(self) -> Decimal:
        rate = self.tax_rate / (1 + self.tax_rate) if self.prices_include_tax else self.tax_rate
        return (self.line_sum * rate).quantize(CENT, ROUND_HALF_UP)

    @property
    def subtotal(self) -> Decimal:
        return self.line_sum - self.tax if self.prices_include_tax else self.line_sum

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.tax + Decimal(self.total_error)

    @property
    def printed_date(self) -> str:
        return self.issued.strftime(self.date_format)

    @property
    def printed_due(self) -> str | None:
        if self.due_days is None:
            return None
        return (self.issued + timedelta(days=self.due_days)).strftime(self.date_format)

    @property
    def initials(self) -> str:
        return "".join(word[0] for word in self.supplier.split()[:2]).upper()

    def printed_fields(self) -> dict:
        """What a perfect extractor should return: only values actually on the page."""
        return {
            "supplier_name": self.supplier,
            "invoice_number": self.number,
            "invoice_date": self.issued.isoformat(),
            "subtotal": None if self.layout == "receipt" else str(self.subtotal),
            "tax": str(self.tax),
            "total": str(self.total),
            "currency": self.currency,
        }


INVOICES = [
    Invoice(
        file="01-northwind-office.pdf", layout="classic",
        scenario="Complete and correct.",
        supplier="Northwind Office Supplies", address="14 Wattle Lane, Parramatta NSW 2150",
        tax_id="ABN 41 602 118 937", customer="Riverbend Dental Clinic", number="INV-1001",
        issued=date(2026, 9, 15), date_format="%d/%m/%Y", currency="AUD",
        lines=[("A4 copy paper (box of 5 reams)", 4, "42.50"),
               ("Ballpoint pens (pack of 50)", 2, "18.90"),
               ("Desk organiser", 3, "24.00")],
        colour=(31, 56, 100), due_days=14,
    ),
    Invoice(
        file="02-bluegum-consulting.pdf", layout="banner",
        scenario="Complete and correct, date written out in words.",
        supplier="Bluegum Consulting", address="Level 3, 88 Flinders Street, Melbourne VIC 3000",
        tax_id="ABN 63 815 270 449", customer="Ironbark Logistics Pty Ltd", number="BGC-2026-044",
        issued=date(2026, 9, 22), date_format="%d %B %Y", currency="AUD",
        lines=[("Process review workshop", 1, "850.00"),
               ("Consulting hours", 12, "165.00")],
        colour=(46, 125, 90), due_days=30,
    ),
    Invoice(
        file="03-harbour-print.pdf", layout="letterhead",
        scenario="Invoice number missing.",
        supplier="Harbour Print Co", address="2/40 Pier Road, Newcastle NSW 2300",
        tax_id="ABN 27 340 991 652", customer="Saltwater Surf School", number=None,
        issued=date(2026, 10, 1), date_format="%d/%m/%Y", currency="AUD",
        lines=[("Business cards (500)", 2, "65.00"),
               ("A3 posters", 25, "3.20")],
        colour=(128, 28, 48), font="Times", due_days=7,
    ),
    Invoice(
        file="04-kestrel-it.pdf", layout="sidebar",
        scenario="Total is $10.00 more than subtotal + tax.",
        supplier="Kestrel IT Services", address="5 Gateway Drive, Brisbane QLD 4000",
        tax_id="ABN 88 154 603 271", customer="Mangrove Accounting", number="K-5521",
        issued=date(2026, 10, 3), date_format="%d %b %Y", currency="AUD",
        lines=[("Laptop setup", 3, "120.00"),
               ("Monthly support plan", 1, "450.00")],
        colour=(88, 56, 140), font="Courier", due_days=14, total_error="10.00",
    ),
    Invoice(
        file="05-coastal-catering.pdf", layout="sidebar",
        scenario="Total is 1 cent off from rounding, within tolerance.",
        supplier="Coastal Catering Co", address="17 Esplanade, Wollongong NSW 2500",
        tax_id="ABN 19 772 045 318", customer="Banksia Community Centre", number="CC-0392",
        issued=date(2026, 10, 6), date_format="%d/%m/%Y", currency="AUD",
        lines=[("Lunch platters", 6, "38.50"),
               ("Fruit platter", 2, "44.95"),
               ("Juice (2L)", 5, "6.85")],
        colour=(222, 99, 72), due_days=7, total_error="0.01",
    ),
    Invoice(
        file="06-summit-freight.pdf", layout="banner",
        scenario="Currency not stated, only a $ sign.",
        supplier="Summit Freight", address="210 Kingsford Smith Drive, Hamilton QLD 4007",
        tax_id="ABN 52 609 334 870", customer="Jacaranda Homewares", number="SF-88013",
        issued=date(2026, 10, 7), date_format="%d/%m/%Y", currency=None,
        lines=[("Pallet freight Sydney to Brisbane", 4, "185.00"),
               ("Fuel levy", 1, "59.20")],
        colour=(214, 110, 20), due_days=30,
    ),
    Invoice(
        file="07-tui-timber.pdf", layout="classic",
        scenario="New Zealand supplier: NZD, 15% GST, ISO date.",
        supplier="Tui Timber Ltd", address="61 Rata Street, Auckland 1010, New Zealand",
        tax_id="GST No. 112-458-903", customer="Kowhai Builders", number="TT-30417",
        issued=date(2026, 10, 9), date_format="%Y-%m-%d", currency="NZD",
        lines=[("Pine framing 90x45 (per metre)", 120, "6.40"),
               ("Delivery", 1, "95.00")],
        colour=(34, 85, 51), font="Times", due_days=20, tax_rate=Decimal("0.15"),
    ),
    Invoice(
        file="08-corner-cafe.pdf", layout="receipt",
        scenario="Receipt with GST-inclusive prices; no subtotal printed.",
        supplier="Corner Cafe", address="3 Market Street, Hobart TAS 7000",
        tax_id="ABN 30 518 207 664", customer="", number="R-0472",
        issued=date(2026, 10, 12), date_format="%d/%m/%Y", currency="AUD",
        lines=[("Flat white", 4, "5.50"),
               ("Banana bread", 2, "6.90")],
        font="Courier", prices_include_tax=True,
    ),
]


def money(amount: Decimal) -> str:
    return f"${amount:,.2f}"


def tint(rgb: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    """Mix a colour with white: 0 = unchanged, 1 = white."""
    return tuple(round(c + (255 - c) * amount) for c in rgb)


def tax_label(inv: Invoice) -> str:
    return f"GST ({inv.tax_rate * 100:.0f}%)"


def details(inv: Invoice) -> list[tuple[str, str]]:
    rows = [("Invoice number", inv.number), ("Invoice date", inv.printed_date), ("Due date", inv.printed_due)]
    return [(label, value) for label, value in rows if value]


def logo(pdf: FPDF, inv: Invoice, x: float, y: float, size: float, on_colour: bool = False) -> None:
    """A circle with the supplier's initials, in brand colour (or white on a coloured background)."""
    fill, text = (WHITE, inv.colour) if on_colour else (inv.colour, WHITE)
    pdf.set_fill_color(*fill)
    pdf.ellipse(x, y, size, size, style="F")
    pdf.set_text_color(*text)
    pdf.set_font(inv.font, "B", size * 1.1)
    pdf.set_xy(x, y)
    pdf.cell(size, size, inv.initials, align="C")
    pdf.set_text_color(*BLACK)


COLUMNS = [("Description", 0.5, "L"), ("Qty", 0.1, "R"), ("Unit price", 0.2, "R"), ("Amount", 0.2, "R")]


def items_table(pdf: FPDF, inv: Invoice, x: float, width: float, style: str) -> None:
    """style: "grid" (all borders), "lines" (a rule under each row) or "striped" (shaded rows)."""
    border = {"grid": 1, "lines": "B", "striped": 0}[style]
    if style == "striped":
        pdf.set_fill_color(*inv.colour)
        pdf.set_text_color(*WHITE)
    elif style == "grid":
        pdf.set_fill_color(*tint(inv.colour, 0.85))
    else:
        pdf.set_text_color(*inv.colour)

    pdf.set_x(x)
    pdf.set_font(inv.font, "B", 10)
    for heading, share, align in COLUMNS:
        pdf.cell(width * share, 8, heading, border=border, align=align, fill=style != "lines")
    pdf.ln()

    pdf.set_text_color(*BLACK)
    pdf.set_fill_color(*tint(inv.colour, 0.9))
    pdf.set_font(inv.font, "", 10)
    for i, (desc, qty, price) in enumerate(inv.lines):
        pdf.set_x(x)
        row = [desc, str(qty), money(Decimal(price)), money(qty * Decimal(price))]
        for value, (_, share, align) in zip(row, COLUMNS):
            pdf.cell(width * share, 7, value, border=border, align=align, fill=style == "striped" and i % 2 == 1)
        pdf.ln()


def totals(pdf: FPDF, inv: Invoice, bar: bool = False) -> None:
    """Subtotal, tax and total, right-aligned. bar=True puts the total on a brand-coloured bar."""
    total_label = f"Total {inv.currency}" if inv.currency else "Total"
    rows = [("Subtotal", inv.subtotal), (tax_label(inv), inv.tax), (total_label, inv.total)]
    pdf.ln(4)
    for i, (label, amount) in enumerate(rows):
        is_total = i == len(rows) - 1
        if bar and is_total:
            pdf.set_fill_color(*inv.colour)
            pdf.set_text_color(*WHITE)
        pdf.set_font(inv.font, "B" if is_total else "", 11)
        pdf.set_x(115)
        pdf.cell(50, 8, label, align="R", fill=bar and is_total)
        pdf.cell(35, 8, money(amount) + " ", align="R", fill=bar and is_total, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*BLACK)


def footer_note(pdf: FPDF, inv: Invoice, text: str, x: float = 10, align: str = "L") -> None:
    pdf.set_xy(x, 280)
    pdf.set_font(inv.font, "I", 8)
    pdf.set_text_color(*tint(BLACK, 0.4))
    pdf.cell(200 - x, 5, text, align=align)
    pdf.set_text_color(*BLACK)


def currency_note(inv: Invoice) -> str:
    return f"All amounts in {inv.currency}. " if inv.currency else ""


def classic(pdf: FPDF, inv: Invoice) -> None:
    """Logo and name top left, a coloured rule, a bordered table."""
    logo(pdf, inv, 10, 10, 16)
    pdf.set_xy(30, 10)
    pdf.set_font(inv.font, "B", 18)
    pdf.set_text_color(*inv.colour)
    pdf.cell(110, 9, inv.supplier)
    pdf.set_text_color(*BLACK)
    pdf.set_font(inv.font, "B", 14)
    pdf.cell(0, 9, "TAX INVOICE", align="R")
    pdf.set_font(inv.font, "", 9)
    for i, text in enumerate([inv.address, inv.tax_id]):
        pdf.set_xy(30, 19 + i * 5)
        pdf.cell(0, 5, text)

    pdf.set_draw_color(*inv.colour)
    pdf.set_line_width(0.8)
    pdf.line(10, 33, 200, 33)
    pdf.set_draw_color(*BLACK)
    pdf.set_line_width(0.2)

    pdf.set_y(40)
    for label, value in details(inv) + [("Bill to", inv.customer)]:
        pdf.set_font(inv.font, "B", 10)
        pdf.cell(35, 6, label)
        pdf.set_font(inv.font, "", 10)
        pdf.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    items_table(pdf, inv, 10, 190, "grid")
    totals(pdf, inv)
    footer_note(pdf, inv, currency_note(inv) + f"Payment due within {inv.due_days} days.")


def banner(pdf: FPDF, inv: Invoice) -> None:
    """A full-width brand-coloured header, two columns of details, a ruled table."""
    pdf.set_fill_color(*inv.colour)
    pdf.rect(0, 0, 210, 36, style="F")
    logo(pdf, inv, 10, 10, 16, on_colour=True)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(30, 9)
    pdf.set_font(inv.font, "B", 20)
    pdf.cell(110, 9, inv.supplier)
    pdf.set_font(inv.font, "", 9)
    for i, text in enumerate([inv.address, inv.tax_id]):
        pdf.set_xy(30, 19 + i * 5)
        pdf.cell(110, 5, text)
    pdf.set_xy(140, 12)
    pdf.set_font(inv.font, "B", 16)
    pdf.cell(60, 10, "INVOICE", align="R")
    pdf.set_text_color(*BLACK)

    pdf.set_xy(10, 46)
    pdf.set_font(inv.font, "B", 9)
    pdf.set_text_color(*inv.colour)
    pdf.cell(110, 5, "BILLED TO")
    pdf.cell(0, 5, "DETAILS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*BLACK)
    pdf.set_font(inv.font, "", 10)
    right = [f"{label}: {value}" for label, value in details(inv)]
    for left, right_text in zip_longest([inv.customer], right, fillvalue=""):
        pdf.cell(110, 6, left)
        pdf.cell(0, 6, right_text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    items_table(pdf, inv, 10, 190, "lines")
    totals(pdf, inv, bar=True)
    footer_note(pdf, inv, currency_note(inv) + "Thank you for your business.", align="C")


def sidebar(pdf: FPDF, inv: Invoice) -> None:
    """A brand-coloured column on the left holding the supplier and invoice details."""
    pdf.set_fill_color(*inv.colour)
    pdf.rect(0, 0, 65, 297, style="F")
    logo(pdf, inv, 10, 12, 18, on_colour=True)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(10, 36)
    pdf.set_font(inv.font, "B", 13)
    pdf.multi_cell(48, 6, inv.supplier, align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(inv.font, "", 8)
    pdf.multi_cell(48, 4.5, f"{inv.address}\n{inv.tax_id}", align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    for label, value in details(inv):
        pdf.set_font(inv.font, "B", 8)
        pdf.cell(48, 5, label.upper(), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(inv.font, "", 11)
        pdf.cell(48, 7, value, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    pdf.set_text_color(*BLACK)

    pdf.set_xy(75, 14)
    pdf.set_font(inv.font, "B", 26)
    pdf.set_text_color(*inv.colour)
    pdf.cell(0, 12, "Invoice", new_x="LEFT", new_y="NEXT")
    pdf.set_text_color(*BLACK)
    pdf.ln(6)
    pdf.set_x(75)
    pdf.set_font(inv.font, "B", 9)
    pdf.cell(0, 5, "BILL TO", new_x="LEFT", new_y="NEXT")
    pdf.set_font(inv.font, "", 11)
    pdf.cell(0, 6, inv.customer)

    pdf.set_y(62)
    items_table(pdf, inv, 75, 125, "striped")
    totals(pdf, inv, bar=True)
    footer_note(pdf, inv, currency_note(inv), x=75)


def letterhead(pdf: FPDF, inv: Invoice) -> None:
    """A centred, formal letterhead with double rules and a bordered table."""
    pdf.set_y(14)
    pdf.set_font(inv.font, "B", 24)
    pdf.set_text_color(*inv.colour)
    pdf.cell(0, 11, inv.supplier, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*BLACK)
    pdf.set_font(inv.font, "", 10)
    pdf.cell(0, 5, f"{inv.address}   |   {inv.tax_id}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*inv.colour)
    for y in (34, 35.2):
        pdf.line(10, y, 200, y)
    pdf.set_draw_color(*BLACK)

    pdf.set_y(40)
    pdf.set_font(inv.font, "I", 15)
    pdf.cell(0, 8, "Tax Invoice", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    right = [f"{label}: {value}" for label, value in details(inv)]
    for left, right_text in zip_longest([f"Billed to: {inv.customer}"], right, fillvalue=""):
        pdf.set_font(inv.font, "", 11)
        pdf.cell(110, 6, left)
        pdf.cell(0, 6, right_text, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    items_table(pdf, inv, 10, 190, "grid")
    totals(pdf, inv)
    footer_note(pdf, inv, currency_note(inv) + "With thanks for your custom.", align="C")


def receipt(pdf: FPDF, inv: Invoice) -> None:
    """A narrow till receipt in a monospace font."""
    def centred(text: str) -> None:
        pdf.cell(0, 5, text, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(inv.font, "B", 12)
    centred(inv.supplier.upper())
    pdf.set_font(inv.font, "", 8)
    centred(inv.address)
    centred(inv.tax_id)
    centred(f"{inv.printed_date}   Receipt {inv.number}")
    centred("-" * 36)
    for desc, qty, price in inv.lines:
        pdf.cell(50, 5, f"{qty} x {desc}")
        pdf.cell(0, 5, f"{qty * Decimal(price):.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
    centred("-" * 36)
    pdf.set_font(inv.font, "B", 10)
    pdf.cell(35, 6, f"TOTAL {inv.currency}")
    pdf.cell(0, 6, money(inv.total), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(inv.font, "", 8)
    centred(f"Includes GST of {money(inv.tax)}")
    centred("Thank you!")


LAYOUTS = {"classic": classic, "banner": banner, "sidebar": sidebar, "letterhead": letterhead, "receipt": receipt}


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    expected = {}
    for inv in INVOICES:
        pdf = FPDF(format=(80, 80) if inv.layout == "receipt" else "A4")
        if inv.layout == "receipt":
            pdf.set_margin(5)
        pdf.set_auto_page_break(False)
        # A fixed creation date, so re-running doesn't change every PDF in git.
        pdf.set_creation_date(datetime.combine(inv.issued, time(), timezone.utc))
        pdf.add_page()
        LAYOUTS[inv.layout](pdf, inv)
        pdf.output(str(OUT_DIR / inv.file))

        fields = inv.printed_fields()
        expected[inv.file] = {"scenario": inv.scenario, "fields": fields, **validate(InvoiceFields(**fields))}

    (OUT_DIR / "expected.json").write_text(json.dumps(expected, indent=2) + "\n")
    for file, result in expected.items():
        print(f"{result['status']:<13} {file}")


if __name__ == "__main__":
    main()
