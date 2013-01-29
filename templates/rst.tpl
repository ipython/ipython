{%- extends 'display_priority.tpl' -%}
{% block in_prompt -%}
In[{{cell.prompt_number if cell.prompt_number else ' '}}]:

.. code:: python

{% endblock in_prompt %}

{% block output_prompt %}{% if cell.haspyout -%}
Out[{{cell.prompt_number}}]:{% endif %}{% endblock output_prompt %}

{% block input %}{{ cell.input | indent}}

{% endblock input %}

{% block pyerr %}{{ super() }}
{% endblock pyerr %}

{% block traceback_line %}
{{ line |indent| rm_ansi }}{% endblock traceback_line %}

{% block pyout %}
.. parsed-literal::

{{ output.text| indent }}
{% endblock pyout %}

{% block stream %}
.. parsed-literal::

{{ output.text| indent }}
{% endblock stream %}




{% block data_svg %}.. image:: {{output.key_svg}}

{% endblock data_svg %}

{% block data_png %}.. image:: {{output.key_png}}

{% endblock data_png %}

{% block data_text scoped %}.. parsed-literal::

{{output.text | indent}}

{% endblock data_text %}

{% block markdowncell scoped %}{{ cell.source | markdown2rst }}
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

{% block rawcell scoped %}{{ cell.source  }}
{% endblock rawcell %}

{% block unknowncell scoped %}
unknown type  {{cell.type}}
{% endblock unknowncell %}
