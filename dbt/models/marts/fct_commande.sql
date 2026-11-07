-- Grain: one row per sale invoice.
--
-- Includes unattributed invoices, because they are real revenue. Anything
-- customer-grained joins through client_id and correctly excludes them; this
-- is the table to use when the question is "how much did we sell".
select
    l.invoice                                       as commande_id,
    d.date_id,
    l.customer_id                                   as client_id,
    l.customer_id is null                           as est_non_attribuee,
    min(l.invoice_at)                               as invoice_at,
    l.invoice_date,
    max(l.country)                                  as pays,
    count(*)                                        as nb_lignes,
    sum(l.quantity)                                 as quantite,
    round(sum(l.montant_ligne), 2)                  as montant
from {{ ref('int_lignes_vente') }} l
left join {{ ref('dim_date') }} d on d.date_complete = l.invoice_date
group by l.invoice, d.date_id, l.customer_id, l.invoice_date
