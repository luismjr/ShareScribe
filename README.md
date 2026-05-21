# ShareScribe

Automated shareholder report generation pipeline. Processes transaction and holdings data through a Perl-based calculation engine and produces formatted PDF statements — one per shareholder account plus a batch summary.

## Pipeline

```
SQLite DB  →  CSV export  →  Perl processor  →  PDF reports
```

1. **Seed** — populates a SQLite database with shareholders, holdings, and transaction history
2. **Export** — dumps raw data to CSV for the Perl processing stage
3. **Process** (`process.pl`) — Perl script calculates per-account, per-ticker summaries: shares bought/sold, net position, total invested, realised gain/loss, dividends, and average cost basis
4. **Generate** — Python/ReportLab renders one formatted PDF per account plus a batch processing report

## Output

Each PDF includes:
- Account holder info and statement date
- Portfolio summary (total invested, proceeds, realised G/L, dividends)
- Current holdings table
- Transaction summary by security with colour-coded gain/loss

## Usage

```bash
pip install -r requirements.txt
python3 pipeline.py
```

PDFs are written to `/output`.

## Stack

| Stage      | Technology              |
|------------|-------------------------|
| Database   | SQLite                  |
| Processing | Perl                    |
| PDF output | Python, ReportLab       |
| Orchestration | Python subprocess    |

## Project Structure

```
ShareScribe/
├── src/
│   ├── seed_db.py          # Seed SQLite with sample data
│   ├── export_csv.py       # Export DB → CSV for Perl
│   ├── process.pl          # Perl: calculate portfolio summaries
│   └── generate_reports.py # Python: render PDF statements
├── data/                   # SQLite DB and intermediate CSVs
├── output/                 # Generated PDF reports
├── pipeline.py             # Run all stages in order
└── requirements.txt
```
