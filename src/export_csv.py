"""
Export raw transaction and holding data from SQLite to CSV
so the Perl processing script can consume it.
"""

import sqlite3
import csv
import os

DB_PATH  = "data/sharescript.db"
TXN_CSV  = "data/transactions.csv"
HOLD_CSV = "data/holdings.csv"


def export():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("""
        SELECT t.id, s.account_number, s.name, t.ticker, t.type,
               COALESCE(t.shares, 0), COALESCE(t.price_per_share, 0),
               t.amount, t.txn_date
        FROM transactions t
        JOIN shareholders s ON s.id = t.shareholder_id
        ORDER BY s.account_number, t.txn_date
    """)
    with open(TXN_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["txn_id","account","name","ticker","type",
                         "shares","price","amount","date"])
        writer.writerows(c.fetchall())

    c.execute("""
        SELECT s.account_number, s.name, h.company, h.ticker,
               h.exchange, h.shares
        FROM holdings h
        JOIN shareholders s ON s.id = h.shareholder_id
        ORDER BY s.account_number
    """)
    with open(HOLD_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["account","name","company","ticker","exchange","shares"])
        writer.writerows(c.fetchall())

    conn.close()
    print(f"Exported: {TXN_CSV}, {HOLD_CSV}")


if __name__ == "__main__":
    export()
