-- Sales lines that can be attributed to a customer.
--
-- Roughly 234,000 of the 1.07M lines carry no customer id. They are real
-- revenue and belong in fct_commande, but they are not people: grouping by a
-- null customer produces a single phantom "customer" holding a fifth of the
-- revenue, which then appears in every segment, every cohort and every
-- lifetime-value figure.
--
-- Splitting this out rather than filtering inside each mart means the rule is
-- written once and the two populations are named, so a reader can see which
-- models are customer-grained and which are not.
select *
from {{ ref('int_lignes_vente') }}
where est_attribuable
