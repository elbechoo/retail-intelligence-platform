-- The product key must be unique case-insensitively, not just exactly.
--
-- A plain `unique` test asks DuckDB, which compares case-sensitively, so
-- '15056BL' and '15056bl' both pass as distinct keys. Power BI's engine
-- compares case-insensitively and treats them as one, then refuses to build
-- the dimension: "contains a duplicate value '15056BL'".
--
-- The warehouse has to guarantee uniqueness under the WEAKEST comparison any
-- consumer will use, not the strongest one its own engine happens to offer.
-- Staging upper-cases the code so this holds; this test is what stops it
-- silently regressing.

select
    upper(produit_id)   as cle_normalisee,
    count(*)            as nb_variantes,
    string_agg(distinct produit_id, ' | ') as variantes
from {{ ref('dim_produit') }}
group by upper(produit_id)
having count(*) > 1
