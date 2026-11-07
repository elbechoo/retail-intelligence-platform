-- One row per raw invoice line, typed and classified. No rows dropped.
--
-- Two things drive the shape of this model.
--
-- First, raw is entirely VARCHAR. DuckDB infers column types from the first
-- rows of the sheet, and the Invoice column begins with plain numbers; the
-- first cancellation, 'C489449', does not appear until row 180, by which
-- point the column has been typed DOUBLE and the read fails. Reading as text
-- and casting here makes every conversion explicit and testable instead of
-- leaving it to inference over a sample.
--
-- Second, nothing is filtered out. Dropping bad rows in staging destroys the
-- evidence that they existed. This model classifies instead: downstream models
-- filter on these flags, so the definition of "a sale" is made once, here, and
-- anyone can query exactly what was excluded and why.

with source as (

    select * from {{ source('raw', 'online_retail') }}

),

typed as (

    select
        trim(invoice)                                       as invoice,
        -- Upper-cased on purpose. The source contains the same product
        -- under both '15056BL' and '15056bl'. DuckDB compares strings
        -- case-sensitively, so they survive as two products and a unique
        -- test on the key passes. Power BI's engine compares
        -- case-INSENSITIVELY, so it sees a duplicate key and refuses to load
        -- the dimension at all.
        --
        -- They are the same product, so the warehouse should say so rather
        -- than leave every downstream consumer to discover the difference.
        -- tests/assert_produit_id_unique_sans_casse.sql guards it.
        upper(trim(stock_code))                             as stock_code,
        nullif(trim(description), '')                       as description,

        {{ texte_vers_entier('quantity') }}                 as quantity,

        -- Excel serial, not a date string. See the macro for why the epoch is
        -- 1899-12-30 rather than 1900-01-01.
        {{ excel_serial_to_timestamp('invoice_date') }}     as invoice_at,
        cast({{ excel_serial_to_timestamp('invoice_date') }} as date) as invoice_date,

        cast(try_cast(price as double) as decimal(12, 4))   as unit_price,

        -- Rendered by Excel as "17850.0", so a direct cast to integer fails.
        {{ texte_vers_entier('customer_id') }}              as customer_id,

        nullif(trim(country), '')                           as country,
        source_sheet
    from source

),

classified as (

    select
        *,

        -- Returns are encoded as a 'C' prefix on the invoice number. There is
        -- no separate returns table; this prefix is the only marker.
        starts_with(invoice, 'C')                           as est_annulation,

        -- Postage, bank charges, manual adjustments, test rows. Including
        -- these in revenue overstates it and pollutes product rankings.
        upper(stock_code) in (
            {%- for code in var('non_product_codes') %}
            '{{ code | upper }}'{{ "," if not loop.last }}
            {%- endfor %}
        )                                                   as est_hors_produit,

        customer_id is not null                             as est_attribuable,
        quantity * unit_price                               as montant_ligne

    from typed

)

select
    *,
    -- Each condition excludes a different kind of row and they are
    -- deliberately kept separate rather than collapsed into one filter.
    (
        not est_annulation
        and not est_hors_produit
        and quantity > 0
        and unit_price > 0
    )                                                       as est_vente,

    (est_annulation and quantity < 0)                       as est_retour

from classified
