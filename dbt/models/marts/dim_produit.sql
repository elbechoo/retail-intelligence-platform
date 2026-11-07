-- Product dimension.
--
-- The same stock code appears with several spellings of its description
-- across two years ("WHITE HANGING HEART T-LIGHT HOLDER" vs typos and case
-- differences). The most frequent description wins, and the count of distinct
-- descriptions is kept as a column so the messiness stays measurable instead
-- of being quietly smoothed over.

with lignes as (
    select * from {{ ref('int_lignes_vente') }}
),

descriptions as (
    select
        stock_code,
        description,
        count(*) as n,
        row_number() over (partition by stock_code order by count(*) desc, description) as rang
    from lignes
    where description is not null
    group by stock_code, description
)

select
    l.stock_code                                    as produit_id,
    d.description                                   as libelle,
    count(distinct d2.description)                  as nb_libelles_distincts,
    count(*)                                        as nb_lignes_vendues,
    sum(l.quantity)                                 as quantite_totale,
    round(sum(l.montant_ligne), 2)                  as chiffre_affaires,
    round(avg(l.unit_price), 4)                     as prix_unitaire_moyen,
    min(l.invoice_date)                             as premiere_vente,
    max(l.invoice_date)                             as derniere_vente
from lignes l
left join descriptions d  on d.stock_code = l.stock_code and d.rang = 1
left join descriptions d2 on d2.stock_code = l.stock_code
group by l.stock_code, d.description
