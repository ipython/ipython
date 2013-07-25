{%- extends 'display_priority.tpl' -%}
{% block in_prompt -%}
In[{{cell.prompt_number if cell.prompt_number else ' '}}]:

.. code:: python

{% endblock in_prompt %}

{% block output_prompt %}{% if cell.haspyout -%}
Out[{{cell.prompt_number}}]:{% endif %}{% endblock output_prompt %}

{% block input %}{{ cell.input | indent}}

{% endblock input %}

{% block pyerr %}::
{{ super() }}
{% endblock pyerr %}

{% block traceback_line %}
{{ line |indent| strip_ansi }}{% endblock traceback_line %}

{% block pyout %}
{% block data_priority scoped %}{{ super()}}{% endblock %}
{% endblock pyout %}

{% block stream %}
.. parsed-literal::

{{ output.text| indent }}
{% endblock stream %}




{% block data_svg %}.. image:: {{output.svg_filename}}

{% endblock data_svg %}

{% block data_png %}.. image:: {{output.png_filename}}

{% endblock data_png %}

{% block data_jpg %}..jpg image:: {{output.jpg_filename}}

{% endblock data_jpg %}



{% block data_latex %}.. math::

{{output.latex| indent}}

{% endblock data_latex %}

{% block data_text scoped %}.. parsed-literal::

{{output.text | indent}}

{% endblock data_text %}

{% block markdowncell scoped %}{{ cell.source | markdown2rst }}
{% endblock markdowncell %}

{% block headingcell scoped %}
{{ ("#" * cell.level + cell.source) | replace('\n', ' ') | markdown2rst }}

{% endblock headingcell %}

{% block rawcell scoped %}{{ cell.source  }}
{% endblock rawcell %}

{% block unknowncell scoped %}
unknown type  {{cell.type}}
{% endblock unknowncell %}
