{%- extends 'null.tpl' -%}

{% block in_prompt %}
# In[{{cell.prompt_number if cell.prompt_number else ' '}}]:{% endblock in_prompt %}

{% block traceback_line %}
{{ line |indent| rm_ansi }}
{% endblock traceback_line %}


{% block pyout %}
{{ output.text| indent | pycomment}}{% endblock pyout %}

{% block stream %}
{{ output.text| indent | pycomment}}
{% endblock stream %}

{% block output_prompt %}# Out[{{cell.prompt_number}}]:{% endblock output_prompt %}


{% block input %}{{ cell.input }}{% endblock input %}

{% block display_data scoped %}
# image file:{% endblock display_data %}

{#
{%  block codecell scoped  %}
# In[{{cell.prompt_number if cell.prompt_number else ' '}}]:
{% if cell.outputs %}
{%- for output in cell.outputs -%}
    {%- if output.output_type in ['pyout','stream']%}

    {%- elif output.output_type in ['display_data'] %}
{{"# image file: fucking display_data"}}
{%- endfor -%}
{% endif %}

{% endblock codecell %}
#}

{% block markdowncell scoped %}
{{ cell.source | pycomment | rm_fake}}{% endblock markdowncell %}

{% block headingcell scoped %}
{{ '#' * cell.level }}{{ cell.source | pycomment}}
{% endblock headingcell %}

{% block rawcell scoped %}
{{ cell.source | pycomment }}
{% endblock rawcell %}

{% block unknowncell scoped %}
unknown type  {{cell.type}}
{% endblock unknowncell %}
