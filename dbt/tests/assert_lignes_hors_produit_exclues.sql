-- Postage and bank charges must never reach the product fact table.
-- Without this, "top products by revenue" eventually returns POSTAGE.
select f.produit_id, count(*) as n
from {{ ref('fct_ligne_commande') }} f
where upper(f.produit_id) in (
    {%- for code in var('non_product_codes') %}
    '{{ code | upper }}'{{ "," if not loop.last }}
    {%- endfor %}
)
group by f.produit_id
