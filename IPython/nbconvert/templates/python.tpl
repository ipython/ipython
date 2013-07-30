{%- extends 'null.tpl' -%}


{% block in_prompt %}
# In[{{ cell.prompt_number if cell.prompt_number else ' ' }}]:
{% endblock in_prompt %}

{% block output_prompt %}
# Out[{{ cell.prompt_number }}]:
{% endblock output_prompt %}

{% block input %}
{{ cell.input | ipython2python }}
{% endblock input %}

{# Those Two are for error displaying
even if the first one seem to do nothing, 
it introduces a new line
#}
{% block pyerr %}
{{ super() }}
{% endblock pyerr %}

{% block traceback_line %}
{{ line | indent | strip_ansi }}
{% endblock traceback_line %}
{# .... #}

{% block pyout %}
{{ output.text | indent | comment_lines }}
{% endblock pyout %}

{% block stream %}
{{ output.text | indent | comment_lines }}
{% endblock stream %}

{% block display_data scoped %}
# image file:
{% endblock display_data %}

{% block markdowncell scoped %}
{{ cell.source | comment_lines }}
{% endblock markdowncell %}

{% block headingcell scoped %}
{{ '#' * cell.level }}{{ cell.source | replace('\n', ' ') | comment_lines }}
{% endblock headingcell %}

{% block rawcell scoped %}
{{ cell.source | comment_lines }}
{% endblock rawcell %}

{% block unknowncell scoped %}
unknown type  {{ cell.type }}
{% endblock unknowncell %}