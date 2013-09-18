{%- extends 'reveal_internals/reveal_cells.tpl' -%}


{%- block any_cell scoped -%}
{%- if cell.metadata.align_type in ['Left'] -%}  
    {{ super() }}
{%- elif cell.metadata.align_type in ['center'] -%}
    <div style="text-align:center">
    {{ super() }}
    </div>
{%- elif cell.metadata.align_type in ['right'] -%}
    <div style="text-align:right">
    {{ super() }}
    </div>
{%- endif -%}   
{%- endblock any_cell -%}
