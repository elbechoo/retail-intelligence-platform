{# Convert an Excel date serial to a real timestamp.

   Excel stores dates as days since 1899-12-30, with the fractional part being
   the time of day. The epoch looks wrong by two days because Excel counts
   from 1900-01-01 as day 1 AND wrongly treats 1900 as a leap year; 1899-12-30
   is the base that cancels both errors out.

   The raw table is all VARCHAR on purpose (see ingest/load_raw.py), so this
   takes text and returns a timestamp.

   try_cast rather than cast: a non-numeric value yields NULL instead of
   failing the build, and the not_null test on the column is what reports it.
   A silent crash in a type conversion tells you less than a failing test. #}

{% macro excel_serial_to_timestamp(colonne) %}
    (
        timestamp '1899-12-30'
        + to_seconds(
            cast(round(try_cast({{ colonne }} as double) * 86400) as bigint)
          )
    )
{% endmacro %}


{# Excel also renders whole numbers as "17850.0", so a direct cast to integer
   fails. Going through double first is the reliable path. #}

{% macro texte_vers_entier(colonne) %}
    cast(round(try_cast({{ colonne }} as double)) as integer)
{% endmacro %}
