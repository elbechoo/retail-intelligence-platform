-- Grain: one row per acquisition cohort per month-offset.
--
-- Cohort retention on real data, which is where it gets interesting: this
-- retailer's customers are mostly wholesale buyers, so retention is far
-- higher than a consumer shop would show, and the December 2010 cohort is
-- truncated because the data stops in December 2011.

with commandes as (
    select
        l.customer_id,
        date_trunc('month', l.invoice_date)::date       as mois_activite,
        p.cohorte_mois
    from {{ ref('int_lignes_vente_client') }} l
    join {{ ref('int_premiere_commande') }} p on p.customer_id = l.customer_id
    group by 1, 2, 3
),

taille_cohorte as (
    select cohorte_mois, count(distinct customer_id) as clients_cohorte
    from {{ ref('int_premiere_commande') }}
    group by cohorte_mois
),

actifs as (
    select
        cohorte_mois,
        mois_activite,
        date_diff('month', cohorte_mois, mois_activite) as mois_depuis_acquisition,
        count(distinct customer_id)                     as clients_actifs
    from commandes
    group by 1, 2, 3
)

select
    a.cohorte_mois,
    a.mois_activite,
    a.mois_depuis_acquisition,
    t.clients_cohorte,
    a.clients_actifs,
    round(a.clients_actifs::double / t.clients_cohorte, 4) as taux_retention
from actifs a
join taille_cohorte t on t.cohorte_mois = a.cohorte_mois
