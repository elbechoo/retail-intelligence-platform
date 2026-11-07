-- Reconciliation: no money may go missing between staging and the marts.
--
-- Two populations, checked separately, because they are deliberately
-- different: fct_ligne_commande holds attributable lines only, fct_commande
-- holds every sale invoice. Checking only one of them would let the other
-- drift unnoticed - which is exactly how the unattributed rows ended up in
-- the customer dimension in the first place.

with attendu_lignes as (
    select round(sum(montant_ligne), 2) as total
    from {{ ref('stg_retail__lines') }}
    where est_vente and est_attribuable
),
obtenu_lignes as (
    select round(sum(montant), 2) as total
    from {{ ref('fct_ligne_commande') }}
),
attendu_commandes as (
    select round(sum(montant_ligne), 2) as total
    from {{ ref('stg_retail__lines') }}
    where est_vente
),
obtenu_commandes as (
    select round(sum(montant), 2) as total
    from {{ ref('fct_commande') }}
)

select 'lignes attribuables' as population, a.total as attendu, o.total as obtenu
from attendu_lignes a, obtenu_lignes o
where abs(a.total - o.total) > 0.01

union all

select 'toutes les ventes', a.total, o.total
from attendu_commandes a, obtenu_commandes o
where abs(a.total - o.total) > 0.01
