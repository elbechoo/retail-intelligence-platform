-- Every customer in the dimension must receive an RFM score. A customer who
-- silently falls out of the segmentation is invisible to every campaign built
-- on it.
select c.client_id
from {{ ref('dim_client') }} c
left join {{ ref('fct_rfm') }} r on r.client_id = c.client_id
where r.client_id is null
