{%- extends 'reveal_internals/align_reveal_cells.tpl' -%}


{%- block any_cell scoped -%}
{%- if 'slide' in cell.metadata.slide_pre_cell_open %}
    <!-- open slide -->  
    <section>
{% endif -%}
    {%- if 'subslide' in cell.metadata.slide_pre_cell_open %} 
        <!-- open subslide -->
        <section>
    {% endif -%}
        {%- if 'fragment' in cell.metadata.slide_pre_cell_open %}
            <div class="fragment">
        {%- endif -%}
                {{ super()|indent(10) }}
        {%- if 'fragment' in cell.metadata.slide_post_cell_close %}
            </div>
        {%- endif -%}
    {%- if 'subslide' in cell.metadata.slide_post_cell_close %}
        <!-- close subslide -->
        </section>
    {% endif -%}
{%- if 'slide' in cell.metadata.slide_post_cell_close %}
    <!-- close slide -->
    </section>
{% endif -%}
{%- endblock any_cell -%}
