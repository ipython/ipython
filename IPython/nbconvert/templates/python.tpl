{%- extends 'null.tpl' -%}

{% block header %}
# coding: utf-8
{% endblock header %}

{% block in_prompt %}
# In[{{ cell.execution_count if cell.execution_count else ' ' }}]:
{% endblock in_prompt %}

{% block input %}
{{ cell.source | ipython2python }}
{% endblock input %}

{% block markdowncell scoped %}
{{ cell.source | comment_lines }}
{% endblock markdowncell %}
