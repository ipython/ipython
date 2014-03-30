{%- extends 'null.tpl' -%}

{% block header %}
# coding: utf-8
{% endblock header %}

{% block in_prompt %}
# In[{{ cell.prompt_number if cell.prompt_number else ' ' }}]:
{% endblock in_prompt %}

{% block input %}
{{ cell.input | ipython2python }}
{% endblock input %}

{% block markdowncell scoped %}
{{ cell.source | comment_lines }}
{% endblock markdowncell %}

{% block headingcell scoped %}
{{ '#' * cell.level }}{{ cell.source | replace('\n', ' ') | comment_lines }}
{% endblock headingcell %}
