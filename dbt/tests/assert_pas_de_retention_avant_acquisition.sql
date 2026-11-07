-- A customer cannot be active before the month they first bought.
select *
from {{ ref('fct_retention_cohorte') }}
where mois_depuis_acquisition < 0
