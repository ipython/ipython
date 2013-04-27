{%- extends 'null.tpl' -%}

{% block in_prompt %}
# In[{{cell.prompt_number if cell.prompt_number else ' '}}]:
{% endblock in_prompt %}

{% block output_prompt %}
# Out[{{cell.prompt_number}}]:{% endblock output_prompt %}

{% block input %}{{ cell.input }}
{% endblock input %}


{# Those Two are for error displaying
even if the first one seem to do nothing, 
it introduces a new line

#}
{% block pyerr %}{{ super() }}
{% endblock pyerr %}

{% block traceback_line %}
{{ line |indent| rm_ansi }}{% endblock traceback_line %}
{# .... #}


{% block pyout %}
{{ output.text| indent | pycomment}}
{% endblock pyout %}

{% block stream %}
{{ output.text| indent | pycomment}}
{% endblock stream %}




{% block display_data scoped %}
# image file:
{% endblock display_data %}

{% block markdowncell scoped %}
{{ cell.source | pycomment }}
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
