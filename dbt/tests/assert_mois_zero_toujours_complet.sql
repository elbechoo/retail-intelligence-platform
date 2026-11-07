-- Every cohort must be 100% retained in its own acquisition month.
--
-- By construction a cohort is defined by its first purchase, so month 0
-- retention is 1.0 by definition. If it is not, the cohort month and the
-- activity month disagree - typically a timezone or date-truncation bug. This
-- is the cheapest possible check that the cohort logic is sound, and it would
-- have caught a date_trunc applied to a timestamp in one place and a date in
-- another.
select
    cohorte_mois,
    clients_cohorte,
    clients_actifs,
    taux_retention
from {{ ref('fct_retention_cohorte') }}
where mois_depuis_acquisition = 0
  and taux_retention <> 1.0
