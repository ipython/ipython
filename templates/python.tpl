{%- extends 'basic.tpl' -%}

{%  block codecell scoped  %}
# In[{{cell.prompt_number if cell.prompt_number else ' '}}]:
{{ cell.input }}
{% if cell.outputs %}
# Out[{{cell.prompt_number}}]:
{%- for output in cell.outputs -%}
    {% if output.output_type in ['pyout','stream']%}
{{ output.text| indent | pycomment}}
    {% elif output.output_type in ['display_data'] %}
{{"# fucking display_data"}}
    {% elif output.output_type in ['pyerr'] %}
{% for line in output.traceback %}
{{ line |indent| rm_ansi}}
{%- endfor -%}
    {%- endif -%}
{%- endfor -%}
{%endif%}

{% endblock codecell %}

{% block markdowncell scoped %}
{{ cell.source | pycomment | rm_fake}}
{% endblock markdowncell %}

{% block headingcell scoped %}
{{ '#' * cell.level }}{{ cell.source | pycomment}}
{% endblock headingcell %}

{% block rawcell scoped %}
{{ cell.source | pycomment }}
{% endblock rawcell %}

{% block unknowncell scoped %}
unknown type  {{cell.type}}
{% endblock unknowncell %}
