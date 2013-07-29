{%- extends 'html_basic.tpl' -%}


{%- block any_cell scoped -%}
{%- if cell.metadata.slide_type in ['-', 'slide', 'subslide'] -%}  
    {{ super() }}
{%- elif cell.metadata.slide_type in ['skip'] -%}
    <div style=display:none>
    {{ super() }}
    </div>
{%- elif cell.metadata.slide_type in ['notes'] -%}
    <aside class="notes">
    {{ super() }}
    </aside>
{%- elif cell.metadata.slide_type in ['fragment'] -%}
    <div class="fragment">
    {{ super() }}
    </div>    
{%- endif -%}   
{%- endblock any_cell -%}
