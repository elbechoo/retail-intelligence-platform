-- Grain: one row per customer. Recency / Frequency / Monetary scoring.
--
-- Recency is measured against the last date in the dataset, not today. Using
-- current_date would make every customer look dormant by several years and
-- the segments would drift every time the model is rebuilt - a classic way to
-- produce a segmentation that quietly changes meaning over time.

with borne as (
    select max(invoice_date) as date_reference
    from {{ ref('int_lignes_vente_client') }}
),

base as (
    select
        c.client_id,
        date_diff('day', c.date_derniere_commande, b.date_reference) as recence_jours,
        c.nb_commandes                                               as frequence,
        c.valeur_vie                                                 as montant
    from {{ ref('dim_client') }} c
    cross join borne b
),

scores as (
    select
        *,
        -- Quintiles. Recency is reversed: fewer days since the last order is
        -- better, so the lowest recency gets the highest score.
        6 - ntile(5) over (order by recence_jours)        as score_recence,
        ntile(5) over (order by frequence, montant)       as score_frequence,
        ntile(5) over (order by montant)                  as score_montant
    from base
)

select
    *,
    score_recence + score_frequence + score_montant      as score_rfm,
    case
        when score_recence >= 4 and score_frequence >= 4 and score_montant >= 4 then 'Champions'
        when score_recence >= 3 and score_frequence >= 3                        then 'Clients fideles'
        when score_recence >= 4 and score_frequence <= 2                        then 'Nouveaux clients'
        when score_recence <= 2 and score_frequence >= 4                        then 'A risque'
        when score_recence <= 2 and score_frequence <= 2                        then 'Perdus'
        else 'A developper'
    end                                                  as segment
from scores
