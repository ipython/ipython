{%- extends 'null.tpl' -%}

{% block in_prompt -%}
In[{{cell.prompt_number if cell.prompt_number else ' '}}]:

.. code:: python

{% endblock in_prompt %}

{% block output_prompt %}
Out[{{cell.prompt_number}}]:{% endblock output_prompt %}

{% block input %}{{ cell.input | indent}}
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
.. parsed-literal::

{{ output.text| indent }}
{% endblock pyout %}

{% block stream %}
.. parsed-literal::

{{ output.text| indent }}
{% endblock stream %}




{% block display_data scoped %}
# image file:
{% endblock display_data %}

{% block markdowncell scoped %}
{{ cell.source | markdown2rst }}
{% endblock markdowncell %}

{% block headingcell scoped %}
{%- set len = cell.source|length -%}
{{ cell.source}}
{% if cell.level == 1 %}
{{- '=' * len }}
{%- elif cell.level == 2 %}
{{- '-' * len }}
{% endif %}
{% endblock headingcell %}

{% block rawcell scoped %}
{{ cell.source  }}
{% endblock rawcell %}

{% block unknowncell scoped %}
unknown type  {{cell.type}}
{% endblock unknowncell %}
