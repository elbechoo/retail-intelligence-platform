"""Export the warehouse marts to Parquet for Power BI.

Power BI reads Parquet natively and keeps the column types, which CSV does
not: dates arrive as dates, decimals as decimals, and nobody has to re-guess
them in Power Query. The files are small enough to commit, so the .pbip in
this repo can be opened and refreshed by anyone who clones it.

Only the marts are exported. Staging and intermediate models are
implementation detail - publishing them would invite a report to be built on
a model that is free to change.

    python analysis/export_for_powerbi.py
"""
from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "retail.duckdb"
OUT = ROOT / "powerbi" / "data"

# Dimensions first, then facts: the order the model should be built in, and
# the order a reader should meet them.
MARTS = [
    "dim_date",
    "dim_client",
    "dim_produit",
    "fct_commande",
    "fct_ligne_commande",
    "fct_rfm",
    "fct_retention_cohorte",
]


def main() -> None:
    if not DB.exists():
        raise SystemExit(
            f"{DB.name} not found. Run `python ingest/load_raw.py` and "
            f"`dbt build` in dbt/ first."
        )

    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)

    total = 0
    print(f"exporting marts to {OUT.relative_to(ROOT)}:")
    for nom in MARTS:
        cible = OUT / f"{nom}.parquet"
        con.execute(
            f"copy (select * from main_marts.{nom}) to '{cible.as_posix()}' "
            f"(format parquet, compression zstd)"
        )
        n = con.execute(f"select count(*) from main_marts.{nom}").fetchone()[0]
        mo = cible.stat().st_size / 1e6
        total += n
        print(f"  {nom:<24} {n:>9,} rows   {mo:>6.2f} MB".replace(",", " "))

    con.close()
    print(f"  {'':<24} {total:>9,} rows total".replace(",", " "))


if __name__ == "__main__":
    main()
