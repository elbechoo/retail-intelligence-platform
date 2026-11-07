-- Customer dimension (Type 1).
--
-- Only customers with at least one attributable sale exist here. The ~25% of
-- rows with no customer id are real revenue and are counted in fct_commande,
-- but they are not people and must not become a phantom customer.

with premiere as (
    select * from {{ ref('int_premiere_commande') }}
),

activite as (
    select
        customer_id,
        count(distinct invoice)                     as nb_commandes,
        count(*)                                    as nb_lignes,
        sum(quantity)                               as quantite_totale,
        round(sum(montant_ligne), 2)                as valeur_vie,
        round(sum(montant_ligne) / nullif(count(distinct invoice), 0), 2) as panier_moyen
    from {{ ref('int_lignes_vente_client') }}
    group by customer_id
),

pays as (
    -- A handful of customers appear under more than one country; take the one
    -- they ordered from most often.
    select customer_id, country
    from (
        select
            customer_id,
            country,
            row_number() over (partition by customer_id order by count(*) desc, country) as rang
        from {{ ref('int_lignes_vente_client') }}
        where country is not null
        group by customer_id, country
    )
    where rang = 1
),

retours as (
    select
        customer_id,
        count(distinct invoice)                     as nb_retours,
        round(sum(montant_retourne), 2)             as montant_retourne
    from {{ ref('int_retours') }}
    where customer_id is not null
    group by customer_id
)

select
    a.customer_id                                   as client_id,
    p.country                                       as pays,
    pr.date_premiere_commande,
    pr.date_derniere_commande,
    pr.cohorte_mois,
    date_diff('day', pr.date_premiere_commande, pr.date_derniere_commande) as duree_vie_jours,
    a.nb_commandes,
    a.nb_lignes,
    a.quantite_totale,
    a.valeur_vie,
    a.panier_moyen,
    coalesce(r.nb_retours, 0)                       as nb_retours,
    coalesce(r.montant_retourne, 0)                 as montant_retourne,
    round(coalesce(r.montant_retourne, 0) / nullif(a.valeur_vie, 0), 4) as taux_retour,
    a.nb_commandes > 1                              as est_recurrent
from activite a
left join premiere pr on pr.customer_id = a.customer_id
left join pays     p  on p.customer_id  = a.customer_id
left join retours  r  on r.customer_id  = a.customer_id
