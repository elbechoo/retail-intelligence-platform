-- How many product codes differ only by letter case?
--
-- Run against the warehouse to size the problem:
--   .\.venv\Scripts\python -c "import duckdb; print(duckdb.connect('retail.duckdb', read_only=True).execute(open('dbt/analyses/verif_casse_produits.sql').read().split('--')[-1]).fetchall())"

select 'codes_distincts=' || count(distinct stock_code)
    || '  distincts_sans_casse=' || count(distinct upper(stock_code))
    || '  collisions=' || (count(distinct stock_code) - count(distinct upper(stock_code)))
  from main_staging.stg_retail__lines
 where est_vente;
