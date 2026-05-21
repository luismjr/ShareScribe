"""
Generate one PDF shareholder report per account from the Perl-processed summary,
plus a batch cover page listing all accounts.
"""

import csv
import os
from collections import defaultdict
from datetime import date

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)

SUMMARY_CSV = "data/summary.csv"
HOLDINGS_CSV = "data/holdings.csv"
OUTPUT_DIR  = "output"

BRAND_BLUE  = colors.HexColor("#003087")
LIGHT_GREY  = colors.HexColor("#F5F5F5")
MID_GREY    = colors.HexColor("#CCCCCC")
GREEN       = colors.HexColor("#1A7A3E")
RED         = colors.HexColor("#C0392B")

REPORT_DATE = date.today().strftime("%B %d, %Y")


def s(name, **kw):
    base = {"fontName": "Helvetica", "fontSize": 9, "leading": 13, "spaceAfter": 2}
    base.update(kw)
    return ParagraphStyle(name, **base)


STYLES = {
    "title":    s("title",  fontSize=18, fontName="Helvetica-Bold",
                  textColor=BRAND_BLUE, alignment=TA_CENTER, spaceAfter=4),
    "subtitle": s("sub",    fontSize=10, textColor=colors.grey,
                  alignment=TA_CENTER, spaceAfter=2),
    "section":  s("sec",    fontSize=11, fontName="Helvetica-Bold",
                  textColor=BRAND_BLUE, spaceBefore=10, spaceAfter=4),
    "body":     s("body"),
    "right":    s("right",  alignment=TA_RIGHT),
    "bold":     s("bold",   fontName="Helvetica-Bold"),
    "small":    s("small",  fontSize=8, textColor=colors.grey),
    "green":    s("green",  fontName="Helvetica-Bold", textColor=GREEN),
    "red":      s("red",    fontName="Helvetica-Bold", textColor=RED),
}


def hr():
    return HRFlowable(width="100%", thickness=0.5,
                      color=MID_GREY, spaceAfter=4, spaceBefore=2)


def fmt_money(v):
    v = float(v)
    sign = "-$" if v < 0 else "$"
    return f"{sign}{abs(v):,.2f}"


def fmt_shares(v):
    return f"{float(v):,.2f}"


def load_summary():
    accounts = defaultdict(list)
    with open(SUMMARY_CSV) as f:
        for row in csv.DictReader(f):
            accounts[row["account"]].append(row)
    return accounts


def load_holdings():
    holdings = defaultdict(list)
    with open(HOLDINGS_CSV) as f:
        for row in csv.DictReader(f):
            holdings[row["account"]].append(row)
    return holdings


def build_report(account, rows, holdings, path):
    name = rows[0]["name"]

    doc = SimpleDocTemplate(
        path, pagesize=letter,
        topMargin=0.6*inch, bottomMargin=0.6*inch,
        leftMargin=0.7*inch, rightMargin=0.7*inch,
    )

    W = letter[0] - 1.4*inch
    story = []

    # --- Header ---
    story.append(Paragraph("ShareScribe", STYLES["title"]))
    story.append(Paragraph("Shareholder Account Statement", STYLES["subtitle"]))
    story.append(Paragraph(f"Generated: {REPORT_DATE}", STYLES["small"]))
    story.append(hr())
    story.append(Spacer(1, 6))

    # Account info
    info_data = [
        [Paragraph("<b>Account Holder</b>", STYLES["bold"]),
         Paragraph(name, STYLES["body"])],
        [Paragraph("<b>Account Number</b>", STYLES["bold"]),
         Paragraph(account, STYLES["body"])],
        [Paragraph("<b>Statement Date</b>", STYLES["bold"]),
         Paragraph(REPORT_DATE, STYLES["body"])],
    ]
    info_table = Table(info_data, colWidths=[W * 0.3, W * 0.7])
    info_table.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # --- Portfolio Summary ---
    story.append(Paragraph("Portfolio Summary", STYLES["section"]))

    total_invested  = sum(float(r["total_invested"])  for r in rows)
    total_proceeds  = sum(float(r["total_proceeds"])  for r in rows)
    total_dividends = sum(float(r["dividends"])        for r in rows)
    total_gain      = sum(float(r["realised_gain_loss"]) for r in rows)

    summary_data = [
        ["Total Invested",          fmt_money(total_invested)],
        ["Total Proceeds from Sales", fmt_money(total_proceeds)],
        ["Realised Gain / Loss",    fmt_money(total_gain)],
        ["Total Dividends Received", fmt_money(total_dividends)],
    ]

    gain_color = GREEN if total_gain >= 0 else RED

    sum_table = Table(summary_data, colWidths=[W * 0.6, W * 0.4])
    sum_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_GREY),
        ("BACKGROUND",   (0, 2), (-1, 2),  colors.white),
        ("FONTNAME",     (0, 2), (-1, 2),  "Helvetica-Bold"),
        ("TEXTCOLOR",    (1, 2), (1, 2),   gain_color),
        ("ALIGN",        (1, 0), (1, -1),  "RIGHT"),
        ("FONTNAME",     (0, 0), (0, -1),  "Helvetica"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (0, -1),  8),
        ("GRID",         (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 10))

    # --- Holdings ---
    story.append(Paragraph("Current Holdings", STYLES["section"]))

    hold_header = ["Company", "Ticker", "Exchange", "Shares Held"]
    hold_rows   = [[h["company"], h["ticker"], h["exchange"],
                    fmt_shares(h["shares"])]
                   for h in holdings]

    hold_table = Table(
        [hold_header] + hold_rows,
        colWidths=[W*0.45, W*0.15, W*0.15, W*0.25]
    )
    hold_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  BRAND_BLUE),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("ALIGN",        (1, 0), (-1, -1), "CENTER"),
        ("ALIGN",        (3, 1), (3, -1),  "RIGHT"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1),  [colors.white, LIGHT_GREY]),
        ("GRID",         (0, 0), (-1, -1), 0.5, MID_GREY),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (0, -1),  6),
    ]))
    story.append(hold_table)
    story.append(Spacer(1, 10))

    # --- Transaction Detail by Ticker ---
    story.append(Paragraph("Transaction Summary by Security", STYLES["section"]))

    txn_header = ["Ticker", "Bought", "Sold", "Net Shares",
                  "Invested", "Proceeds", "Gain/Loss", "Dividends", "Avg Cost"]
    txn_data   = []

    for r in rows:
        gain   = float(r["realised_gain_loss"])
        g_text = fmt_money(gain)
        txn_data.append([
            r["ticker"],
            fmt_shares(r["shares_bought"]),
            fmt_shares(r["shares_sold"]),
            fmt_shares(r["net_shares"]),
            fmt_money(r["total_invested"]),
            fmt_money(r["total_proceeds"]),
            g_text,
            fmt_money(r["dividends"]),
            fmt_money(r["avg_cost_basis"]),
        ])

    txn_col_w = [W*0.08, W*0.09, W*0.09, W*0.09,
                 W*0.12, W*0.12, W*0.12, W*0.12, W*0.17]
    txn_table = Table([txn_header] + txn_data, colWidths=txn_col_w)

    gain_styles = []
    for i, r in enumerate(rows):
        gain = float(r["realised_gain_loss"])
        clr  = GREEN if gain >= 0 else RED
        gain_styles.append(("TEXTCOLOR", (6, i+1), (6, i+1), clr))
        gain_styles.append(("FONTNAME",  (6, i+1), (6, i+1), "Helvetica-Bold"))

    txn_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  BRAND_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
        ("ALIGN",         (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN",         (0, 0), (0, -1),  "CENTER"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("GRID",          (0, 0), (-1, -1), 0.5, MID_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ] + gain_styles))
    story.append(txn_table)

    # --- Footer ---
    story.append(Spacer(1, 16))
    story.append(hr())
    story.append(Paragraph(
        "This statement is generated automatically by ShareScribe. "
        "For questions regarding your account, please contact your registered agent.",
        STYLES["small"]
    ))

    doc.build(story)


def build_batch_summary(accounts_data, path):
    doc = SimpleDocTemplate(
        path, pagesize=letter,
        topMargin=0.6*inch, bottomMargin=0.6*inch,
        leftMargin=0.7*inch, rightMargin=0.7*inch,
    )
    W = letter[0] - 1.4*inch
    story = []

    story.append(Paragraph("ShareScribe", STYLES["title"]))
    story.append(Paragraph("Batch Processing Report", STYLES["subtitle"]))
    story.append(Paragraph(f"Generated: {REPORT_DATE}", STYLES["small"]))
    story.append(hr())
    story.append(Spacer(1, 10))

    story.append(Paragraph("Accounts Processed", STYLES["section"]))

    rows = [["Account", "Holder Name", "Securities", "Total Invested",
             "Realised G/L", "Dividends"]]

    for account, data_rows in sorted(accounts_data.items()):
        name      = data_rows[0]["name"]
        n_sec     = len(data_rows)
        invested  = sum(float(r["total_invested"])      for r in data_rows)
        gain      = sum(float(r["realised_gain_loss"])  for r in data_rows)
        dividends = sum(float(r["dividends"])            for r in data_rows)
        rows.append([account, name, str(n_sec),
                     fmt_money(invested), fmt_money(gain), fmt_money(dividends)])

    col_w = [W*0.14, W*0.28, W*0.1, W*0.16, W*0.16, W*0.16]
    t = Table(rows, colWidths=col_w)

    gain_styles = []
    for i, row in enumerate(rows[1:], start=1):
        gain_val = float(row[4].replace("$","").replace(",","").replace("-",""))
        if "-" in row[4]:
            gain_val = -gain_val
        clr = GREEN if gain_val >= 0 else RED
        gain_styles.append(("TEXTCOLOR", (4, i), (4, i), clr))
        gain_styles.append(("FONTNAME",  (4, i), (4, i), "Helvetica-Bold"))

    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  BRAND_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ALIGN",         (2, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("GRID",          (0, 0), (-1, -1), 0.5, MID_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (1, -1),  6),
    ] + gain_styles))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        f"Total accounts processed: <b>{len(accounts_data)}</b>",
        STYLES["body"]
    ))

    story.append(Spacer(1, 16))
    story.append(hr())
    story.append(Paragraph(
        "ShareScribe automated batch report. Individual account PDFs available in /output.",
        STYLES["small"]
    ))

    doc.build(story)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    accounts  = load_summary()
    holdings  = load_holdings()

    for account, rows in accounts.items():
        path = os.path.join(OUTPUT_DIR, f"{account}.pdf")
        build_report(account, rows, holdings[account], path)
        print(f"Generated: {path}")

    batch_path = os.path.join(OUTPUT_DIR, "batch_summary.pdf")
    build_batch_summary(accounts, batch_path)
    print(f"Generated: {batch_path}")


if __name__ == "__main__":
    main()
