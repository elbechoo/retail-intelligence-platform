"""Generate the Power BI column/relationship script from the warehouse schema.

Creating a table from an M expression defines a partition, not a schema: TOM
does not infer columns the way Power BI Desktop's Get Data wizard does. They
have to be declared.

Declaring ~70 columns by hand would be tedious and, worse, would be a second
copy of the schema free to drift from the marts. Instead this reads the real
column list out of DuckDB and emits the commands, so the model's shape is
derived from the warehouse rather than restated alongside it. Change a mart,
re-run this, and the model follows.

    python analysis/generate_model_script.py      # writes powerbi/build_columns.ps1
"""
from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "retail.duckdb"
SORTIE = ROOT / "powerbi" / "build_columns.ps1"

TABLES = [
    "dim_date", "dim_client", "dim_produit",
    "fct_commande", "fct_ligne_commande", "fct_rfm", "fct_retention_cohorte",
]

# One key per table, used for --is-key and for the relationship wiring below.
CLES = {
    "dim_date": "date_id",
    "dim_client": "client_id",
    "dim_produit": "produit_id",
    "fct_commande": "commande_id",
    "fct_ligne_commande": "ligne_id",
    "fct_rfm": "client_id",
}

RELATIONS = [
    ("fct_ligne_commande", "date_id",    "dim_date",    "date_id"),
    ("fct_ligne_commande", "client_id",  "dim_client",  "client_id"),
    ("fct_ligne_commande", "produit_id", "dim_produit", "produit_id"),
    ("fct_commande",       "date_id",    "dim_date",    "date_id"),
    ("fct_commande",       "client_id",  "dim_client",  "client_id"),
    ("fct_rfm",            "client_id",  "dim_client",  "client_id"),
]


def type_pbi(duck: str) -> str:
    """Map a DuckDB type to a Power BI data type.

    DECIMAL maps to decimal rather than double on purpose: montant is money,
    and the dbt suite reconciles revenue to the penny. Loading it as a float
    would give that guarantee away at the very last step, which is the kind of
    thing nobody notices until two reports disagree by a few pence.
    """
    d = duck.upper()
    if d.startswith("DECIMAL") or d.startswith("NUMERIC"):
        return "decimal"
    if d in {"BIGINT", "INTEGER", "SMALLINT", "TINYINT", "HUGEINT", "UBIGINT", "UINTEGER"}:
        return "int64"
    if d in {"DOUBLE", "FLOAT", "REAL"}:
        return "double"
    if d == "BOOLEAN":
        return "boolean"
    if d.startswith("DATE") or d.startswith("TIMESTAMP"):
        return "datetime"
    return "string"


def format_pbi(nom: str, type_duck: str) -> str | None:
    d = type_duck.upper()
    if d.startswith("DECIMAL") or d.startswith("NUMERIC"):
        return "#,##0.00"
    if nom.startswith("taux_") or nom.startswith("est_"):
        return None
    if d in {"BIGINT", "INTEGER", "SMALLINT", "HUGEINT"} and not nom.endswith("_id"):
        return "#,##0"
    return None


def echap(s: str) -> str:
    """PowerShell single-quoted strings escape a quote by doubling it."""
    return s.replace("'", "''")


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"{DB.name} not found - build the warehouse first.")

    con = duckdb.connect(str(DB), read_only=True)
    lignes: list[str] = []
    total = 0

    lignes.append("""<#
    GENERATED FILE - do not edit by hand.
    Produced by analysis/generate_model_script.py from the DuckDB marts.

    Declares every column on the Power BI tables, marks the date table, and
    wires the relationships. Tables and measures are created by
    powerbi/build_model.ps1; run that first.

    Requires Power BI Desktop open on the .pbip and `pbi connect` done.
#>

$ErrorActionPreference = "Stop"
$echecs = @()

function Invoke-Pbi {
    param([string]$Etape, [scriptblock]$Commande)
    try {
        $sortie = & $Commande 2>&1
        if ($LASTEXITCODE -ne 0) { throw ($sortie | Out-String) }
    } catch {
        $script:echecs += [pscustomobject]@{ Etape = $Etape; Erreur = ($_ | Out-String).Trim() }
    }
}
""")

    for table in TABLES:
        cols = con.execute(f"describe select * from main_marts.{table}").fetchall()
        cle = CLES.get(table)
        lignes.append(f'\nWrite-Host "{table} ({len(cols)} columns)"')
        for nom, type_duck, *_ in cols:
            t = type_pbi(type_duck)
            fmt = format_pbi(nom, type_duck)
            morceaux = [
                "pbi column create", f"'{echap(nom)}'",
                "-t", f"'{table}'",
                "--data-type", t,
                "--source-column", f"'{echap(nom)}'",
            ]
            if fmt:
                morceaux += ["--format-string", f"'{fmt}'"]
            if nom == cle:
                morceaux.append("--is-key")
            cmd = " ".join(morceaux)
            lignes.append(f'Invoke-Pbi "{table}.{nom}" {{ {cmd} }}')
            total += 1

    # Refresh so the partitions actually load now that a schema exists.
    lignes.append('\nWrite-Host "`nRefreshing"')
    for table in TABLES:
        lignes.append(f'Invoke-Pbi "refresh {table}" {{ pbi table refresh {table} }}')

    lignes.append('\nWrite-Host "`nDate table"')
    lignes.append('Invoke-Pbi "mark dim_date" '
                  '{ pbi table mark-date dim_date --date-column date_complete }')

    lignes.append('\nWrite-Host "`nRelationships"')
    for ft, fc, tt, tc in RELATIONS:
        lignes.append(
            f'Invoke-Pbi "{ft}.{fc} -> {tt}.{tc}" {{ '
            f'pbi relationship create --from-table {ft} --from-column {fc} '
            f'--to-table {tt} --to-column {tc} }}'
        )

    lignes.append("""
Write-Host "`n--------------------------------------------------"
if ($echecs.Count -eq 0) {
    Write-Host "All steps succeeded." -ForegroundColor Green
} else {
    Write-Host "$($echecs.Count) step(s) failed:" -ForegroundColor Yellow
    $echecs | Select-Object -First 12 | ForEach-Object {
        Write-Host "`n  * $($_.Etape)" -ForegroundColor Yellow
        Write-Host "    $(($_.Erreur -split "`n")[0..1] -join ' ')"
    }
}
""")

    con.close()
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text("\n".join(lignes), encoding="utf-8")
    print(f"wrote {SORTIE.relative_to(ROOT)}")
    print(f"  {total} columns across {len(TABLES)} tables")
    print(f"  {len(RELATIONS)} relationships")


if __name__ == "__main__":
    main()
