{%- extends 'html_basic.tpl' -%}

{% block body %}
<div class="notebook">
{{ super() }}
</div>
{%- endblock body %}


{% block input %}
<div class="input_area box-flex1">
<pre class="prettyprint lang-python">
{{ cell.input | escape_for_html }}
</pre>
</div>
{%- endblock input %}
