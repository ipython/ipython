{%- extends 'align_reveal_cells.tpl' -%}



{%- block any_cell scoped -%}
{%- if cell.metadata.slide_type in ['subslide'] -%}  
    <section>
{%- endif -%}
    
{{ super() }}
    
{%- if cell.metadata.slide_helper in ['subslide_end'] -%}
    </section>
{%- endif -%}
{%- endblock any_cell -%}
