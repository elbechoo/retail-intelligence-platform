# Retail Analytics Warehouse

An analytics-engineering project on **real** retail data: dbt models over
DuckDB, building a dimensional warehouse with RFM segmentation and cohort
retention, every layer covered by tests that run in CI.

`git clone`, one command to load the data, one command to build. No database
server, no cloud account, no credentials.

## Data

[Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
from the UCI Machine Learning Repository: roughly **1.07 million real invoice
lines** from a UK-based online gift retailer, 01/12/2009 to 09/12/2011. Mostly
wholesale buyers rather than consumers, which is why retention here is far
higher than a consumer shop would show.

The raw file is not committed. `ingest/load_raw.py` fetches it from UCI and
loads it into DuckDB unchanged — a pipeline that cannot re-fetch its own input
is not a pipeline.

## Output

Every chart below is rendered straight from the warehouse by
`analysis/make_charts.py` and committed as SVG. They are not drawn in a tool
and pasted in, so they cannot quietly go stale: re-run the script after a
build and the picture follows the data.

Hand-written SVG rather than matplotlib - no extra dependency to install, the
output is text so git can diff it, and GitHub renders it inline.

### Where the rows go

![Composition of the raw lines](charts/qualite_donnees.svg)

The chart to read first. A line in the file is not a sale, and the distance
between those two numbers is most of the work on this project.

### Revenue by month

![Monthly revenue](charts/revenu_mensuel.svg)

The November peak is real, not a seasonality weight someone typed in: this is
a UK gift wholesaler shipping stock to retailers before Christmas.

### Lifetime value by RFM segment

![RFM segments](charts/segments_rfm.svg)

### Cohort retention

![Cohort retention](charts/retention_cohortes.svg)

Cohorts under 30 customers are excluded. A cohort of four can only ever show
0%, 25%, 50% or 75%, which looks like dramatic movement on a heatmap and means
nothing. Later cohorts are truncated by the end of the data - that is the
dataset ending, not customers leaving.

## What makes this dataset worth the trouble

It is genuinely messy, and handling the mess correctly is the actual work:

| Reality in the data | How it is handled |
|---|---|
| Returns are encoded as a `C` prefix on the invoice number — there is no returns table | Flagged `est_annulation` in staging, surfaced as `int_retours` with the sign flipped |
| ~25% of rows have no customer ID | Real revenue, so kept in `fct_commande`; excluded from everything customer-grained so they never become a phantom customer |
| `POST`, `BANK CHARGES`, `M`, `D`, test rows share the product code column | Classified `est_hors_produit`; a test fails the build if any reach the product fact table |
| Negative quantities and zero prices occur outside cancellations | Excluded from sales by explicit, separate conditions rather than one catch-all filter |
| The same product appears under several spellings across two years | Most frequent description wins; the count of variants is kept as a column so the messiness stays measurable |

Staging **drops no rows**. It classifies them. Dropping bad rows destroys the
evidence that they existed; every downstream model filters on the flags, so
the definition of "a sale" is made once and anyone can query what was excluded.

## Model graph

```
raw.online_retail  (1.07M lines, untouched)
        │
        └── stg_retail__lines ......... typed + classified, nothing dropped
                 │
                 ├── int_lignes_vente ....... the single definition of "a sale"
                 ├── int_retours ............ cancellations, sign flipped
                 └── int_premiere_commande .. first/last order per customer
                          │
   ┌──────────────────────┼─────────────────────────┐
   │                      │                         │
 dim_date            dim_client               dim_produit
 fct_commande        fct_ligne_commande       fct_rfm
                     fct_retention_cohorte
```

`int_premiere_commande` exists so that `dim_client` and
`fct_retention_cohorte` cannot disagree about when a customer joined. A cohort
that disagrees with the customer dimension is a bug waiting to happen, so the
question is answered in exactly one place.

## Tests

Generic tests on keys, relationships, ranges and accepted values, plus five
singular tests that encode things that must be true of *this* business:

- **`assert_ca_marts_egale_source`** — revenue in the fact table equals revenue
  in staging, to the penny. This is the one that catches a silently dropped
  join. Every other test checks a property; this checks that no money went
  missing between source and mart.
- **`assert_mois_zero_toujours_complet`** — every cohort is 100% retained in its
  own acquisition month. True by construction, so if it fails, the cohort month
  and the activity month disagree — typically a date-truncation bug.
- **`assert_pas_de_retention_avant_acquisition`** — nobody is active before they
  first bought.
- **`assert_clients_rfm_complets`** — every customer gets a score. A customer who
  falls out of the segmentation is invisible to every campaign built on it.
- **`assert_lignes_hors_produit_exclues`** — postage never reaches the product
  fact table. Without it, "top products by revenue" eventually returns POSTAGE.

## Analysis in the warehouse

**RFM segmentation** (`fct_rfm`) — quintile scores on recency, frequency and
monetary value, into six segments. Recency is measured against the last date in
the dataset, not `current_date`: using today would make every customer look
dormant by years, and the segment boundaries would silently shift every time
the model was rebuilt.

**Cohort retention** (`fct_retention_cohorte`) — monthly acquisition cohorts by
months-since-first-order. Later cohorts are truncated by the end of the data;
that is a property of the dataset, not a finding.

## The bug that only Power BI could find

`dim_produit.produit_id` passed dbt's `unique` test and Power BI still refused
to load the table:

> Column 'produit_id' in Table 'dim_produit' contains a duplicate value '15056BL'

Both engines were right. **DuckDB compares strings case-sensitively**, so
`15056BL` and `15056bl` are two products and the key is unique. **Power BI's
engine compares case-insensitively**, so they are one product and the key is
not.

The fix belongs in the warehouse, not the report: staging now upper-cases the
stock code, because they are the same product and the warehouse should say so
rather than leave every consumer to find out separately. 170 codes merged;
4,901 products became 4,731.

`tests/assert_produit_id_unique_sans_casse.sql` stops it regressing. The
general rule it encodes is worth more than the specific fix:

> A warehouse must guarantee its keys under the **weakest** comparison any
> consumer will use, not the strongest one its own engine happens to offer.

## Power BI model

`powerbi/` holds a `.pbip` project: the semantic model as TMDL and the report
as PBIR, both plain text in the repository.

The model is not clicked together and saved. It is **built by script**:

| Script | What it does |
|---|---|
| `powerbi/build_model.ps1` | Creates the 7 tables with Power Query pointed at the Parquet exports, and the 11 DAX measures |
| `analysis/generate_model_script.py` | Reads the column list out of DuckDB and generates the next script, so the model's shape is derived from the marts rather than restated beside them |
| `powerbi/build_columns.ps1` | Declares every column with its type, refreshes, marks the date table, creates the 6 relationships |

Both run against a live Power BI Desktop instance through
[pbi-cli](https://github.com/MinaSaad1/pbi-cli).

Why bother, when the UI is faster the first time: a model built by clicking
exists only as a binary, and a measure change arrives in review as a
screenshot. Built this way, every measure carries its reasoning next to the
DAX - why `DIVIDE` rather than `/`, why `dim_date` must be marked, why
`fct_retention_cohorte` is deliberately left unrelated - and a reviewer can
read the diff.

`DECIMAL` maps to `decimal`, not `double`. `montant` is money and the dbt
suite reconciles revenue to the penny; loading it as a float would give that
guarantee away at the final step.

### The report

`powerbi/build_report.ps1` builds the Overview page: four KPI cards, revenue
by month, revenue by RFM segment, and a product table. The report layer writes
PBIR JSON directly, so it needs no Power BI connection - close Desktop before
running it or Desktop will write the files back from memory.

Each visual lands in its own `visual.json`, which is the point: moving a chart
or rebinding a field shows up as a diff on one small file instead of a new
binary.

The line chart plots `dim_date[annee_mois]`, a 'YYYY-MM' string, rather than
`date_complete`. It sorts chronologically as text, so the axis is right
without a sort-by-column, and the chart has 25 points instead of 761.

The numbers on the page reconcile with the warehouse: GBP 17.4M revenue and
5,852 customers on the cards match `dbt run-operation print_resume` exactly.
`Orders` reads ~37K rather than 39,516 because it counts attributable
invoices; the unattributed ones live in `fct_commande` by design.

### Running it

```powershell
python analysis/export_for_powerbi.py      # marts -> powerbi/data/*.parquet
# open powerbi/Retail Analytics.pbip in Power BI Desktop
pbi connect
.\powerbi\build_model.ps1
python analysis/generate_model_script.py
.\powerbi\build_columns.ps1
```

The Parquet exports are not committed: they are derived data, 22 MB of it, and
stale the moment a model changes. Run the export before opening the project.

## Running it

```bash
pip install -r requirements.txt
python ingest/load_raw.py          # downloads ~45 MB from UCI, loads to DuckDB

cd dbt
dbt deps   --profiles-dir .
dbt build  --profiles-dir .        # runs every model and every test
cd ..

python analysis/make_charts.py     # re-render the README charts from the marts
```

Then query it with anything that speaks DuckDB:

```sql
select segment, count(*) as clients, round(sum(montant)) as valeur
from fct_rfm join dim_client using (client_id)
group by segment order by valeur desc;
```

## Headline figures

Produced by `dbt run-operation print_resume`, which runs in CI on every push,
so these cannot drift away from what the warehouse actually contains.

| Measure | Value |
|---|---|
| Raw invoice lines loaded | 1,067,371 |
| Sale lines, attributable | 802,634 |
| Sale invoices | 39,516 |
| Customers | 5,852 |
| Products | 4,731 |
| Revenue, attributable lines | GBP 17,434,464.73 |
| Invoices with no customer ID | 2,922 |
| Customers scored "Champions" | 1,335 |
| Date range | 2009-12-01 to 2011-12-09 |

Two of those numbers deserve a note rather than a victory lap.

**802,634 of 1,067,371.** A quarter of the raw lines are not attributable
sales: cancellations, non-product codes such as postage and bank charges,
zero-price rows, and the ~234,000 lines with no customer ID. The gap between
the two figures is the work.

**Revenue is attributable only.** The 2,922 unattributed invoices are real
revenue and sit in `fct_commande`; they are excluded from the customer-grained
figure above because they are not people. Quoting one number for both would be
wrong in whichever direction you picked.

## Stack

dbt 1.9 · DuckDB · dbt_utils · GitHub Actions

## Notes

Data is used under the UCI Machine Learning Repository's terms and is not
redistributed here. Figures describe this dataset only and are not a claim
about retail in general.
