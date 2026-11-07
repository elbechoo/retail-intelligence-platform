<#
    Build the Retail Analytics semantic model from nothing, as a script.

    The point of this file: a Power BI model built by clicking exists only as
    a binary, and a measure change shows up in review as a screenshot. Built
    this way, the model is a script someone can read, diff and re-run, and the
    TMDL it produces is text in the repository.

    Prerequisites
      1. python analysis/export_for_powerbi.py     (writes powerbi/data/*.parquet)
      2. Power BI Desktop open on powerbi/Retail Analytics.pbip
      3. pbi connect

    Usage
      .\powerbi\build_model.ps1
      .\powerbi\build_model.ps1 -DataFolder "D:\somewhere\else\data"

    Re-running is destructive: it drops and recreates the tables it manages.
#>

[CmdletBinding()]
param(
    # Where the Parquet exports live. Power Query cannot discover the .pbip's
    # own location, so the path is baked into each table's M at build time.
    # That is why this script, not the TMDL, is the portable artifact: clone
    # the repo, re-run this, and the paths are correct for your machine.
    [string]$DataFolder = (Join-Path $PSScriptRoot "data")
)

$ErrorActionPreference = "Stop"
$echecs = @()

function Invoke-Pbi {
    <# Run a pbi command, record failures, keep going.

       Stopping at the first error would leave the model half-built and the
       next run would hit "already exists" on everything before the failure.
       Collecting failures and reporting them at the end is friendlier. #>
    param([string]$Etape, [scriptblock]$Commande)
    Write-Host "  $Etape" -NoNewline
    try {
        $sortie = & $Commande 2>&1
        if ($LASTEXITCODE -ne 0) { throw ($sortie | Out-String) }
        Write-Host "  ok" -ForegroundColor Green
    } catch {
        Write-Host "  FAILED" -ForegroundColor Red
        $script:echecs += [pscustomobject]@{ Etape = $Etape; Erreur = ($_ | Out-String).Trim() }
    }
}

$DataFolder = (Resolve-Path $DataFolder).Path
if (-not (Test-Path (Join-Path $DataFolder "dim_date.parquet"))) {
    throw "No parquet found in $DataFolder. Run: python analysis\export_for_powerbi.py"
}
Write-Host "`nData folder: $DataFolder`n"

# ---------------------------------------------------------------- tables ---
# Marts only. Staging and intermediate stay out of the model on purpose:
# publishing them would invite a report to be built on something free to change.
$tables = @(
    @{ nom = "dim_date";              desc = "Conformed date dimension, one row per day" },
    @{ nom = "dim_client";            desc = "Customer dimension, attributable customers only" },
    @{ nom = "dim_produit";           desc = "Product dimension, one row per stock code sold" },
    @{ nom = "fct_commande";          desc = "Grain: one sale invoice, including unattributed" },
    @{ nom = "fct_ligne_commande";    desc = "Grain: one attributable sale line" },
    @{ nom = "fct_rfm";               desc = "Grain: one customer, RFM scores and segment" },
    @{ nom = "fct_retention_cohorte"; desc = "Grain: one acquisition cohort per month offset" }
)

Write-Host "Tables"
foreach ($t in $tables) {
    $chemin = Join-Path $DataFolder "$($t.nom).parquet"
    # M has no escape character for backslashes; only quotes are doubled.
    $m = @"
let
    Source = Parquet.Document(File.Contents("$chemin"))
in
    Source
"@
    Invoke-Pbi "$($t.nom)" { $m | pbi table create $t.nom --m-expression - --description $t.desc }
}

# ------------------------------------------------------- date intelligence ---
# Without a marked date table, time functions silently use an auto-generated
# hidden calendar per date column, and SAMEPERIODLASTYEAR gives wrong answers
# at the edges of the range.
Write-Host "`nDate table"
Invoke-Pbi "mark dim_date" { pbi table mark-date dim_date --column date_complete }

# --------------------------------------------------------- relationships ---
# Many-side first. Every fact joins to the dimensions on surrogate keys built
# in dbt, so there is nothing to clean up here.
Write-Host "`nRelationships"
$relations = @(
    @{ ft = "fct_ligne_commande";    fc = "date_id";    tt = "dim_date";     tc = "date_id" },
    @{ ft = "fct_ligne_commande";    fc = "client_id";  tt = "dim_client";   tc = "client_id" },
    @{ ft = "fct_ligne_commande";    fc = "produit_id"; tt = "dim_produit";  tc = "produit_id" },
    @{ ft = "fct_commande";          fc = "date_id";    tt = "dim_date";     tc = "date_id" },
    @{ ft = "fct_commande";          fc = "client_id";  tt = "dim_client";   tc = "client_id" },
    @{ ft = "fct_rfm";               fc = "client_id";  tt = "dim_client";   tc = "client_id" }
)
foreach ($r in $relations) {
    Invoke-Pbi "$($r.ft).$($r.fc) -> $($r.tt).$($r.tc)" {
        pbi relationship create --from-table $r.ft --from-column $r.fc `
                                --to-table $r.tt --to-column $r.tc
    }
}

# fct_retention_cohorte is deliberately left unrelated. Its grain is a cohort
# month as text ("2010-03"), not a date, so any join to dim_date would be a
# guess that silently filters the wrong rows. It is queried on its own.

# ----------------------------------------------------------------- measures ---
# All amounts are GBP. Format strings avoid the currency symbol so the file
# stays ASCII and survives PowerShell's encoding defaults.
Write-Host "`nMeasures"
$mesures = @(
    @{ nom = "Total Revenue";  tbl = "fct_ligne_commande"; fmt = "#,##0";
       dax = "SUM ( fct_ligne_commande[montant] )";
       desc = "Revenue from attributable sale lines, GBP. Excludes unattributed invoices - use fct_commande for those." },

    @{ nom = "Orders";  tbl = "fct_ligne_commande"; fmt = "#,##0";
       dax = "DISTINCTCOUNT ( fct_ligne_commande[commande_id] )";
       desc = "Distinct invoices containing attributable sale lines." },

    @{ nom = "Customers";  tbl = "fct_ligne_commande"; fmt = "#,##0";
       dax = "DISTINCTCOUNT ( fct_ligne_commande[client_id] )";
       desc = "Distinct customers who bought in the current filter context." },

    @{ nom = "Units Sold";  tbl = "fct_ligne_commande"; fmt = "#,##0";
       dax = "SUM ( fct_ligne_commande[quantite] )";
       desc = "Total units across attributable sale lines." },

    @{ nom = "Average Order Value";  tbl = "fct_ligne_commande"; fmt = "#,##0.00";
       dax = "DIVIDE ( [Total Revenue], [Orders] )";
       desc = "DIVIDE, not /, so an empty filter context returns blank rather than an error." },

    @{ nom = "Revenue per Customer";  tbl = "fct_ligne_commande"; fmt = "#,##0.00";
       dax = "DIVIDE ( [Total Revenue], [Customers] )";
       desc = "Revenue divided by distinct buying customers." },

    @{ nom = "Lines per Order";  tbl = "fct_ligne_commande"; fmt = "#,##0.0";
       dax = "DIVIDE ( COUNTROWS ( fct_ligne_commande ), [Orders] )";
       desc = "Basket breadth: distinct products per invoice." },

    @{ nom = "Returning Customers";  tbl = "fct_ligne_commande"; fmt = "#,##0";
       dax = "CALCULATE ( DISTINCTCOUNT ( dim_client[client_id] ), dim_client[est_recurrent] = TRUE () )";
       desc = "Customers with more than one order over their lifetime." },

    @{ nom = "Returning Customer Rate";  tbl = "fct_ligne_commande"; fmt = "0.0%";
       dax = "DIVIDE ( [Returning Customers], DISTINCTCOUNT ( dim_client[client_id] ) )";
       desc = "Share of customers who ordered more than once. High here because the buyers are mostly wholesale." },

    @{ nom = "Revenue LY";  tbl = "fct_ligne_commande"; fmt = "#,##0";
       dax = "CALCULATE ( [Total Revenue], SAMEPERIODLASTYEAR ( dim_date[date_complete] ) )";
       desc = "Requires dim_date to be marked as the date table." },

    @{ nom = "Revenue YoY %";  tbl = "fct_ligne_commande"; fmt = "0.0%";
       dax = "DIVIDE ( [Total Revenue] - [Revenue LY], [Revenue LY] )";
       desc = "Blank where there is no prior year - the data starts in December 2009." }
)

foreach ($m in $mesures) {
    Invoke-Pbi "$($m.nom)" {
        $m.dax | pbi measure create $m.nom --table $m.tbl --expression - `
                     --format-string $m.fmt --description $m.desc --folder "Sales"
    }
}

# ------------------------------------------------------------------ report ---
Write-Host "`n--------------------------------------------------"
if ($echecs.Count -eq 0) {
    Write-Host "Model built with no failures." -ForegroundColor Green
} else {
    Write-Host "$($echecs.Count) step(s) failed:" -ForegroundColor Yellow
    $echecs | ForEach-Object {
        Write-Host "`n  * $($_.Etape)" -ForegroundColor Yellow
        Write-Host "    $($_.Erreur)"
    }
}
Write-Host @"

Next:
  pbi table list
  pbi measure list
  pbi database export-tmdl "powerbi\Retail Analytics.SemanticModel\definition"
"@
