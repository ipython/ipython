{%- extends 'display_priority.tpl' -%}


{% block in_prompt %}
{% endblock in_prompt %}

{% block output_prompt %}
{% endblock output_prompt %}

{% block input %}
{%- if cell.input.strip() -%}
.. code:: python

{{ cell.input | indent}}
{%- endif -%}
{% endblock input %}

{% block pyerr %}
::

{{ super() }}
{% endblock pyerr %}

{% block traceback_line %}
{{ line | indent | strip_ansi }}
{% endblock traceback_line %}

{% block pyout %}
{% block data_priority scoped %}
{{ super() }}
{% endblock %}
{% endblock pyout %}

{% block stream %}
.. parsed-literal::

{{ output.text | indent }}
{% endblock stream %}

{% block data_svg %}
.. image:: {{ output.svg_filename|urlencode }}
{% endblock data_svg %}

{% block data_png %}
.. image:: {{ output.png_filename|urlencode }}
{% endblock data_png %}

{% block data_jpg %}
.. image:: {{ output.jpeg_filename|urlencode }}
{% endblock data_jpg %}

{% block data_latex %}
.. math::

{{ output.latex | strip_dollars | indent }}
{% endblock data_latex %}

{% block data_text scoped %}
.. parsed-literal::

{{ output.text | indent }}
{% endblock data_text %}

{% block data_html scoped %}
.. raw:: html

{{ output.html | indent }}
{% endblock data_html %}

{% block markdowncell scoped %}
{{ cell.source | markdown2rst }}
{% endblock markdowncell %}

{% block headingcell scoped %}
{{ ("#" * cell.level + cell.source) | replace('\n', ' ') | markdown2rst }}
{% endblock headingcell %}

{% block unknowncell scoped %}
unknown type  {{cell.type}}
{% endblock unknowncell %}
