{%- extends 'basic.tpl' -%}

{% block codecell scoped  %}
{% block in_prompt %}{% endblock in_prompt %}
{% block input %}{% endblock input %}
{% if cell.outputs %}
{% block output_prompt %}{% endblock output_prompt %}
{%- for output in cell.outputs -%}
    {%- if output.output_type in ['pyout']%}
        {% block pyout scoped %}{% endblock pyout %}
    {%- elif output.output_type in ['stream'] %}
        {% block stream scoped %}{% endblock stream %}
    {%- elif output.output_type in ['display_data'] %}
        {% block display_data scoped %}{% endblock display_data %}
    {%- elif output.output_type in ['pyerr'] %}
        {% block pyerr scoped %}
        {%- for line in output.traceback %}
            {% block traceback_line scoped %}
            {% endblock traceback_line %}
        {%- endfor %}
        {% endblock pyerr %}
    {%- endif %}
{%- endfor -%}
{% endif %}

{% endblock codecell %}

{% block markdowncell scoped %}
{% endblock markdowncell %}

{% block headingcell scoped %}
{% endblock headingcell %}

{% block rawcell scoped %}
{% endblock rawcell %}

{% block unknowncell scoped %}
{% endblock unknowncell %}
