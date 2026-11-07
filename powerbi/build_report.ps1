<#
    Build the Overview report page from nothing, as a script.

    Same argument as build_model.ps1: a report laid out by dragging exists
    only as a binary, and a layout change arrives in review as a screenshot.
    Built this way the page is a script someone can read and re-run, and the
    PBIR JSON it produces is text in the repository.

    No Power BI Desktop connection needed - the report layer writes PBIR
    files directly. Close Desktop before running so it does not overwrite
    the files from memory.

    Usage
      .\powerbi\build_report.ps1
#>

[CmdletBinding()]
param(
    [string]$ReportPath = (Join-Path $PSScriptRoot "Retail Analytics.Report"),
    [string]$PageDisplayName = "Overview"
)

$ErrorActionPreference = "Stop"
$echecs = @()

function Invoke-Pbi {
    param([string]$Etape, [scriptblock]$Commande)
    Write-Host ("  {0,-42}" -f $Etape) -NoNewline
    try {
        $sortie = & $Commande 2>&1
        if ($LASTEXITCODE -ne 0) { throw ($sortie | Out-String) }
        Write-Host "ok" -ForegroundColor Green
    } catch {
        Write-Host "FAILED" -ForegroundColor Red
        $script:echecs += [pscustomobject]@{ Etape = $Etape; Erreur = ($_ | Out-String).Trim() }
    }
}

# ------------------------------------------------------------------ page ---
# Find the page by display name rather than hardcoding its generated ID, so
# the script survives the page being recreated.
$pagesJson = pbi --json report --path $ReportPath list-pages | Out-String
$pages = ($pagesJson | ConvertFrom-Json)
$page = $pages | Where-Object { $_.display_name -eq $PageDisplayName } | Select-Object -First 1

if (-not $page) {
    Write-Host "Creating page '$PageDisplayName'"
    pbi report --path $ReportPath add-page -d $PageDisplayName | Out-Null
    $pages = (pbi --json report --path $ReportPath list-pages | Out-String | ConvertFrom-Json)
    $page = $pages | Where-Object { $_.display_name -eq $PageDisplayName } | Select-Object -First 1
}
$pageId = $page.name
Write-Host "`nPage '$PageDisplayName' ($pageId), $($page.width)x$($page.height)`n"

# --------------------------------------------------------------- KPI cards ---
# Four across the top. 1280 wide: 20px margins, 290 wide, 20px gutters.
Write-Host "Cards"
$cartes = @(
    @{ n = "card_revenue";   f = "fct_ligne_commande[Total Revenue]";        x =  20 },
    @{ n = "card_orders";    f = "fct_ligne_commande[Orders]";               x = 330 },
    @{ n = "card_customers"; f = "fct_ligne_commande[Customers]";            x = 640 },
    @{ n = "card_aov";       f = "fct_ligne_commande[Average Order Value]";  x = 950 }
)
foreach ($c in $cartes) {
    Invoke-Pbi $c.n {
        pbi visual --path $ReportPath add --page $pageId --type card -n $c.n --x $c.x --y 20 --width 290 --height 120
    }
    Invoke-Pbi "$($c.n) <- $($c.f)" {
        pbi visual --path $ReportPath bind $c.n --page $pageId --field $c.f
    }
}

# ------------------------------------------------------------------ charts ---
Write-Host "`nCharts"

# Revenue over time. annee_mois is a 'YYYY-MM' string, which sorts correctly
# as text, so the axis reads chronologically without extra sort-by config.
Invoke-Pbi "revenue by month (line)" {
    pbi visual --path $ReportPath add --page $pageId --type line_chart -n "line_revenue_mois" `
        --x 20 --y 160 --width 760 --height 250
}
Invoke-Pbi "  bind dim_date[annee_mois]" {
    pbi visual --path $ReportPath bind "line_revenue_mois" --page $pageId `
        --category "dim_date[annee_mois]" --value "fct_ligne_commande[Total Revenue]"
}

# Revenue by RFM segment.
Invoke-Pbi "revenue by segment (bar)" {
    pbi visual --path $ReportPath add --page $pageId --type bar_chart -n "bar_segments" `
        --x 800 --y 160 --width 460 --height 250
}
Invoke-Pbi "  bind fct_rfm[segment]" {
    pbi visual --path $ReportPath bind "bar_segments" --page $pageId `
        --category "fct_rfm[segment]" --value "fct_ligne_commande[Total Revenue]"
}

# Products. Left unfiltered here; a Top N filter is added below so the table
# shows the products worth looking at rather than all 4,731.
Invoke-Pbi "products (table)" {
    pbi visual --path $ReportPath add --page $pageId --type table -n "table_produits" `
        --x 20 --y 430 --width 1240 --height 270
}
Invoke-Pbi "  bind dim_produit[libelle]" {
    pbi visual --path $ReportPath bind "table_produits" --page $pageId `
        --column "dim_produit[libelle]" --value "fct_ligne_commande[Total Revenue]"
}

# ------------------------------------------------------------------ report ---
Write-Host "`n--------------------------------------------------"
if ($echecs.Count -eq 0) {
    Write-Host "Report page built with no failures." -ForegroundColor Green
} else {
    Write-Host "$($echecs.Count) step(s) failed:" -ForegroundColor Yellow
    $echecs | ForEach-Object {
        Write-Host "`n  * $($_.Etape)" -ForegroundColor Yellow
        Write-Host "    $((($_.Erreur -split "`n") | Select-Object -First 2) -join ' ')"
    }
}
Write-Host @"

Next:
  pbi report --path "$ReportPath" validate
  then open powerbi\Retail Analytics.pbip in Power BI Desktop
"@
