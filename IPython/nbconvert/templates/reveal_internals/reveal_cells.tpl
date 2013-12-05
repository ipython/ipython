{%- extends 'html_basic.tpl' -%}

{%- block any_cell scoped %}
{%- if cell.metadata.slide_type in ['-', 'fragment', 'slide', 'subslide'] %}  
    {{ super()|indent(4) }}
{% elif cell.metadata.slide_type in ['skip'] %}
    <div style="display:none">
        {{ super()|indent(8) }}
    </div>
{% elif cell.metadata.slide_type in ['notes'] %}
    <aside class="notes">
        {{ super()|indent(8) }}
    </aside>
{% endif -%}
{%- endblock any_cell -%}
