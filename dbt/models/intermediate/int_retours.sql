-- Return lines, with the quantity flipped positive so returns can be summed
-- without every consumer remembering the sign convention.
select
    *,
    -quantity        as quantite_retournee,
    -montant_ligne   as montant_retourne
from {{ ref('stg_retail__lines') }}
where est_retour
  and not est_hors_produit
