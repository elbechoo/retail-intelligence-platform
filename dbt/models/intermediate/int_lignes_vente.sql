-- Sales lines only. The single definition of "a sale" used by every mart.
select *
from {{ ref('stg_retail__lines') }}
where est_vente
