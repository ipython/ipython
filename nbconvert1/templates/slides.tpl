{%- extends 'subslides.tpl' -%}



{%- block any_cell scoped -%}
{%- if cell.metadata.slide_type in ['slide'] -%}  
    <section>
    <section>
{%- endif -%}
    
{{ super() }}
    
{%- if cell.metadata.slide_helper in ['slide_end'] -%}
    </section>
    </section>
{%- endif -%}
{%- endblock any_cell -%}
