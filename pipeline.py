#!/usr/bin/env python3
"""
ShareScribe pipeline — run all stages in order:
  1. Seed SQLite database with sample data
  2. Export raw data to CSV for Perl processing
  3. Run Perl script to calculate portfolio summaries
  4. Generate PDF reports for each shareholder + batch summary
"""

import subprocess
import sys
import os


def run(label, *cmd):
    print(f"\n[{label}]")
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"Error in stage '{label}'. Aborting.", file=sys.stderr)
        sys.exit(result.returncode)


def main():
    print("=" * 50)
    print("  ShareScribe — Automated Report Pipeline")
    print("=" * 50)

    run("1/4  Seeding database",  sys.executable, "src/seed_db.py")
    run("2/4  Exporting CSV",     sys.executable, "src/export_csv.py")
    run("3/4  Processing (Perl)", "perl",          "src/process.pl")
    run("4/4  Generating PDFs",   sys.executable, "src/generate_reports.py")

    pdfs = [f for f in os.listdir("output") if f.endswith(".pdf")]
    print(f"\nDone. {len(pdfs)} PDF(s) written to /output")


if __name__ == "__main__":
    main()
