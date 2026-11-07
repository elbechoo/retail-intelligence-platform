-- Conformed date dimension over the dataset's own span.
with spine as (
    select unnest(generate_series(
        date '{{ var("date_start") }}',
        date '{{ var("date_end") }}',
        interval 1 day
    ))::date as date_complete
)

select
    cast(strftime(date_complete, '%Y%m%d') as integer) as date_id,
    date_complete,
    extract(year    from date_complete)                as annee,
    extract(month   from date_complete)                as mois,
    extract(quarter from date_complete)                as trimestre,
    strftime(date_complete, '%Y-%m')                   as annee_mois,
    date_trunc('month', date_complete)::date           as debut_mois,
    extract(isodow  from date_complete)                as jour_semaine_num,
    strftime(date_complete, '%A')                      as jour_semaine,
    extract(isodow from date_complete) >= 6            as est_weekend
from spine
