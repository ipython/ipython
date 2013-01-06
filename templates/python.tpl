{%- extends 'null.tpl' -%}

{% block in_prompt %}
# In[{{cell.prompt_number if cell.prompt_number else ' '}}]:
{% endblock in_prompt %}

{% block traceback_line %}
{{ line |indent| rm_ansi }}
{% endblock traceback_line %}


{% block pyout %}
{{ output.text| indent | pycomment}}
{% endblock pyout %}


{#
{%  block codecell scoped  %}
# In[{{cell.prompt_number if cell.prompt_number else ' '}}]:
{{ cell.input }}
{% if cell.outputs %}
# Out[{{cell.prompt_number}}]:
{%- for output in cell.outputs -%}
    {%- if output.output_type in ['pyout','stream']%}

    {%- elif output.output_type in ['display_data'] %}
{{"# image file: fucking display_data"}}
{%- endfor -%}
{% endif %}

{% endblock codecell %}
#}

{% block markdowncell scoped %}
{#{{ cell.source | pycomment | rm_fake}}#}
{% endblock markdowncell %}

{% block headingcell scoped %}
{#{{ '#' * cell.level }}{{ cell.source | pycomment}}#}
{% endblock headingcell %}

{% block rawcell scoped %}
{#{{ cell.source | pycomment }}#}
{% endblock rawcell %}

{% block unknowncell scoped %}
{#unknown type  {{cell.type}}#}
{% endblock unknowncell %}
