{%- block header -%}
{%- endblock header -%}
{%- block body -%}
{%- for cell in cells -%}
    {%- block any_cell scoped -%}
        {%- if cell.type in ['code'] -%}
            {%- block codecell scoped-%}
            {%- endblock codecell-%}
        {%- elif cell.type in ['markdown'] -%}
            {%- block markdowncell scoped-%}
            {%- endblock markdowncell -%}
        {%- elif cell.type in ['heading'] -%}
            {%- block headingcell scoped-%}
            {%- endblock headingcell -%}
        {%- elif cell.type in ['raw'] -%}
            {%- block rawcell scoped-%}
            {%- endblock rawcell -%}
        {%- else -%}
            {%- block unknowncell scoped-%}
            {%- endblock unknowncell -%}
        {%- endif -%}
    {%- endblock any_cell -%}
{%- endfor -%}
{%- endblock body -%}

{%- block footer -%}
{%- endblock footer -%}
