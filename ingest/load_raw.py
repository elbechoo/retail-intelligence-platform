"""Download the real Online Retail II dataset and load it into DuckDB.

Source: UCI Machine Learning Repository, "Online Retail II"
        https://archive.ics.uci.edu/dataset/502/online+retail+ii

Real transactions from a UK-based online gift retailer, 01/12/2009 - 09/12/2011.
Roughly 1,067,000 invoice lines, split across two yearly sheets.

The raw file is NOT committed: it is ~45 MB, it is not mine to redistribute,
and a pipeline that cannot re-fetch its own input is not a pipeline.

The Excel file is read by DuckDB directly rather than through pandas. One
fewer dependency, no dataframe round-trip for a million rows, and the load is
SQL - which is the right language for it.

    python ingest/load_raw.py
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import duckdb
import requests

URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "retail.duckdb"
XLSX = RAW_DIR / "online_retail_II.xlsx"

# The workbook's two sheets. Two years of the same business, not two datasets.
SHEETS = ["Year 2009-2010", "Year 2010-2011"]


def download() -> Path:
    """Fetch the archive once and keep it; re-running is a no-op."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if XLSX.exists():
        print(f"already present: {XLSX} ({XLSX.stat().st_size / 1e6:.1f} MB)")
        return XLSX

    zip_path = RAW_DIR / "online_retail_II.zip"
    print(f"downloading {URL}")
    with requests.get(URL, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(zip_path, "wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
    print(f"  {zip_path.stat().st_size / 1e6:.1f} MB")

    with zipfile.ZipFile(zip_path) as z:
        name = next(n for n in z.namelist() if n.endswith(".xlsx"))
        with z.open(name) as src, open(XLSX, "wb") as dst:
            dst.write(src.read())
    zip_path.unlink()
    return XLSX


def load(xlsx: Path) -> None:
    con = duckdb.connect(str(DB_PATH))
    con.execute("INSTALL excel")
    con.execute("LOAD excel")
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("DROP TABLE IF EXISTS raw.online_retail")

    # Source columns carry spaces and mixed case ("Customer ID"), so they are
    # quoted and renamed once here. Everything else stays exactly as supplied:
    # cleaning belongs in dbt where it is tested and visible, not hidden in a
    # loader script.
    # all_varchar: DuckDB infers column types from the first rows, and the
    # Invoice column starts with plain numbers (489434...). The first
    # cancellation, 'C489449', does not appear until row 180 - by which point
    # the column has already been typed DOUBLE and the read fails.
    #
    # Rather than fight the inference, everything is read as text and every
    # cast is made explicit in staging, where it is visible and tested. Raw
    # stays a faithful copy of the file.
    select_tpl = """
        select
            "Invoice"      as invoice,
            "StockCode"    as stock_code,
            "Description"  as description,
            "Quantity"     as quantity,
            "InvoiceDate"  as invoice_date,
            "Price"        as price,
            "Customer ID"  as customer_id,
            "Country"      as country,
            '{sheet}'      as source_sheet
        from read_xlsx('{path}', sheet = '{sheet}', all_varchar = true)
    """
    path = xlsx.as_posix()
    union_sql = "\nunion all\n".join(
        select_tpl.format(sheet=s, path=path) for s in SHEETS
    )

    print("reading both sheets with DuckDB (one pass, no dataframe)")
    con.execute(f"CREATE TABLE raw.online_retail AS {union_sql}")

    rows = con.execute("""
        select source_sheet, count(*) as n
        from raw.online_retail group by source_sheet order by source_sheet
    """).fetchall()
    for sheet, n in rows:
        print(f"  {sheet}: {n:,} rows")


    # Print what the date column actually looks like. Excel sometimes hands
    # over a serial number ("40179.32") rather than a datetime string, and the
    # staging cast has to know which.
    print("\n  sample invoice_date values as stored:")
    for (v,) in con.execute(
        "select distinct invoice_date from raw.online_retail "
        "where invoice_date is not null limit 5"
    ).fetchall():
        print(f"    {v!r}")
    print("\n  sample invoice values (cancellations included):")
    for (v,) in con.execute(
        "select distinct invoice from raw.online_retail "
        "where starts_with(invoice, 'C') limit 3"
    ).fetchall():
        print(f"    {v!r}")
    print()
    total = con.execute("select count(*) from raw.online_retail").fetchone()[0]
    con.close()
    print(f"loaded {total:,} rows into {DB_PATH.name}:raw.online_retail")


if __name__ == "__main__":
    try:
        load(download())
    except requests.HTTPError as exc:
        print(f"download failed: {exc}", file=sys.stderr)
        print("UCI is occasionally down. Retry, or place the file manually at "
              "data/raw/online_retail_II.xlsx.", file=sys.stderr)
        raise SystemExit(1)
    except duckdb.Error as exc:
        print(f"load failed: {exc}", file=sys.stderr)
        print("If the sheet names differ, list them with:\n"
              "  duckdb -c \"install excel; load excel; "
              "select * from read_xlsx_sheet_names('data/raw/online_retail_II.xlsx');\"",
              file=sys.stderr)
        raise SystemExit(1)
