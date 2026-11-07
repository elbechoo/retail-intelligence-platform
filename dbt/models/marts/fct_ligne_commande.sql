-- Grain: one row per attributable sale line.
--
-- Two things worth knowing about the key.
--
-- The source genuinely contains repeated identical lines: the same product,
-- same invoice, same timestamp, appearing more than once. 41,775 key
-- collisions on (invoice, stock_code, invoice_at) say so. They are not a load
-- error - re-scanning an item writes another line - so they are kept and the
-- grain is made explicit with an occurrence number rather than deduplicated
-- away. Silently collapsing them would quietly reduce revenue.
--
-- Unattributed lines are excluded here because this table joins to
-- dim_client. Their revenue is not lost: fct_commande carries every sale
-- invoice, attributed or not.

with lignes as (

    select
        *,
        row_number() over (
            partition by invoice, stock_code, invoice_at
            order by quantity, unit_price
        ) as numero_occurrence
    from {{ ref('int_lignes_vente_client') }}

)

select
    {{ dbt_utils.generate_surrogate_key([
        'invoice', 'stock_code', 'invoice_at', 'numero_occurrence'
    ]) }}                                           as ligne_id,
    l.invoice                                       as commande_id,
    l.numero_occurrence,
    d.date_id,
    l.customer_id                                   as client_id,
    l.stock_code                                    as produit_id,
    l.invoice_at,
    l.invoice_date,
    l.quantity                                      as quantite,
    l.unit_price                                    as prix_unitaire,
    round(l.montant_ligne, 2)                       as montant,
    l.country                                       as pays,
    l.source_sheet
from lignes l
left join {{ ref('dim_date') }} d on d.date_complete = l.invoice_date
