{# Prints the headline numbers straight from the warehouse.

   Every figure quoted in the README is produced by this macro in CI, so the
   README cannot drift away from what the data actually says. If a number in
   the README is wrong, this output contradicts it in public. #}

{% macro print_resume() %}

  {% set requete %}
    select
      (select count(*)                    from {{ ref('fct_ligne_commande') }})   as lignes_vente,
      (select count(*)                    from {{ ref('fct_commande') }})         as commandes,
      (select count(*)                    from {{ ref('dim_client') }})           as clients,
      (select count(*)                    from {{ ref('dim_produit') }})          as produits,
      (select round(sum(montant), 2)      from {{ ref('fct_ligne_commande') }})   as ca_total,
      (select count(*)                    from {{ ref('fct_commande') }} where est_non_attribuee) as commandes_non_attribuees,
      (select count(*)                    from {{ ref('fct_rfm') }} where segment = 'Champions')  as champions,
      (select min(invoice_date)           from {{ ref('fct_ligne_commande') }})   as date_min,
      (select max(invoice_date)           from {{ ref('fct_ligne_commande') }})   as date_max
  {% endset %}

  {% if execute %}
    {% set resultats = run_query(requete) %}
    {% do log("", info=true) %}
    {% do log("=== Chiffres du warehouse ===", info=true) %}
    {% for colonne in resultats.column_names %}
      {% do log("  " ~ colonne ~ " = " ~ resultats.columns[colonne].values()[0], info=true) %}
    {% endfor %}
    {% do log("", info=true) %}
  {% endif %}

{% endmacro %}
