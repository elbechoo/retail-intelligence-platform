-- First and last purchase per customer. Used by both dim_client and the
-- cohort mart, so it is defined once: a cohort that disagrees with the
-- customer dimension about when someone joined is a bug waiting to happen.
select
    customer_id,
    min(invoice_date)                               as date_premiere_commande,
    max(invoice_date)                               as date_derniere_commande,
    date_trunc('month', min(invoice_date))::date    as cohorte_mois
from {{ ref('int_lignes_vente_client') }}
group by customer_id
