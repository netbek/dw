{% macro full_mask(expression, data_type) -%}
    {{ adapter.dispatch('full_mask')(expression, data_type) }}
{%- endmacro %}


{% macro clickhouse__full_mask(expression, data_type) -%}
    case
        when false then {{ expression }}
        else {{ dbt_privacy.mask(expression) }}
    end
{%- endmacro %}
