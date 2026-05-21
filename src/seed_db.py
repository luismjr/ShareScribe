"""
Seed the ShareScribe SQLite database with sample shareholders,
holdings, and transaction history.
"""

import sqlite3
import random
from datetime import date, timedelta

DB_PATH = "data/sharescript.db"

SHAREHOLDERS = [
    (1, "Margaret Chen",    "m.chen@email.com",    "ACC-001"),
    (2, "David Okafor",     "d.okafor@email.com",  "ACC-002"),
    (3, "Sarah Kowalski",   "s.kowalski@email.com","ACC-003"),
    (4, "James Thornton",   "j.thornton@email.com","ACC-004"),
    (5, "Priya Nair",       "p.nair@email.com",    "ACC-005"),
]

COMPANIES = [
    ("Royal Bank of Canada",      "RY",  "TSX"),
    ("Shopify Inc.",               "SHOP","TSX"),
    ("Enbridge Inc.",              "ENB", "TSX"),
    ("Canadian National Railway", "CNR", "TSX"),
    ("BCE Inc.",                   "BCE", "TSX"),
]

def random_date(start_year=2022, end_year=2025):
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript("""
        DROP TABLE IF EXISTS shareholders;
        DROP TABLE IF EXISTS holdings;
        DROP TABLE IF EXISTS transactions;

        CREATE TABLE shareholders (
            id             INTEGER PRIMARY KEY,
            name           TEXT NOT NULL,
            email          TEXT NOT NULL,
            account_number TEXT UNIQUE NOT NULL
        );

        CREATE TABLE holdings (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            shareholder_id INTEGER NOT NULL,
            company        TEXT NOT NULL,
            ticker         TEXT NOT NULL,
            exchange       TEXT NOT NULL,
            shares         REAL NOT NULL,
            FOREIGN KEY (shareholder_id) REFERENCES shareholders(id)
        );

        CREATE TABLE transactions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            shareholder_id INTEGER NOT NULL,
            ticker         TEXT NOT NULL,
            type           TEXT NOT NULL CHECK(type IN ('BUY','SELL','DIVIDEND')),
            shares         REAL,
            price_per_share REAL,
            amount         REAL NOT NULL,
            txn_date       TEXT NOT NULL,
            FOREIGN KEY (shareholder_id) REFERENCES shareholders(id)
        );
    """)

    c.executemany(
        "INSERT INTO shareholders VALUES (?,?,?,?)",
        SHAREHOLDERS
    )

    random.seed(42)
    holding_rows = []
    txn_rows     = []

    for sh_id, _, _, _ in SHAREHOLDERS:
        for company, ticker, exchange in COMPANIES:
            shares = round(random.uniform(10, 500), 2)
            holding_rows.append((sh_id, company, ticker, exchange, shares))

            # 3-6 buy/sell transactions per holding
            for _ in range(random.randint(3, 6)):
                txn_type = random.choice(["BUY", "BUY", "SELL"])
                txn_shares = round(random.uniform(1, 50), 2)
                price      = round(random.uniform(20, 200), 2)
                amount     = round(txn_shares * price, 2)
                txn_rows.append((
                    sh_id, ticker, txn_type,
                    txn_shares, price, amount,
                    str(random_date())
                ))

            # 1-3 dividend payments
            for _ in range(random.randint(1, 3)):
                amount = round(random.uniform(10, 300), 2)
                txn_rows.append((
                    sh_id, ticker, "DIVIDEND",
                    None, None, amount,
                    str(random_date())
                ))

    c.executemany(
        "INSERT INTO holdings (shareholder_id,company,ticker,exchange,shares) VALUES (?,?,?,?,?)",
        holding_rows
    )
    c.executemany(
        "INSERT INTO transactions (shareholder_id,ticker,type,shares,price_per_share,amount,txn_date) VALUES (?,?,?,?,?,?,?)",
        txn_rows
    )

    conn.commit()
    conn.close()
    print(f"Database seeded: {DB_PATH}")

if __name__ == "__main__":
    seed()
