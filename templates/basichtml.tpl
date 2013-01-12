{%- extends 'null.tpl' -%}



{% block codecell %}
<div class="cell border-box-sizing code_cell vbox">
{{ super() }}</div>
{%- endblock codecell %}

{% block input_group -%}
<div class="input hbox">
{{super()}}
</div>
{% endblock input_group %}

{% block output_group -%}
<div class="vbox output_wrapper">
<div class="output vbox">
<div class="hbox output_area">
{{ super() }}
</div>
</div>
</div>
{% endblock output_group %}


{% block in_prompt -%}
<div class="prompt input_prompt">In&nbsp;[{{cell.prompt_number}}]:</div>
{%- endblock in_prompt %}

{% block output_prompt -%}
<div class="prompt output_prompt">
{%- if cell.haspyout -%}
Out[{{cell.prompt_number}}]:
{%- endif -%}
</div>
{% endblock output_prompt %}

{% block input %}
<div class="input_area box-flex1">
{{cell.input | highlight }}
</div>
{%- endblock input %}


{% block markdowncell scoped %}
<div class="text_cell_render border-box-sizing rendered_html">
{{ cell.source | markdown| rm_fake}}
</div>
{%- endblock markdowncell %}

{% block headingcell scoped %}
<div class="text_cell_render border-box-sizing rendered_html">
<h{{cell.level}}>
  {{cell.source}}
</h{{cell.level}}>
</div>
{% endblock headingcell %}

{% block rawcell scoped %}
{{ cell.source }}
{% endblock rawcell %}

{% block unknowncell scoped %}
unknown type  {{cell.type}}
{% endblock unknowncell %}


{% block pyout -%}
<div class="output_subarea output_pyout">
<pre>{{output.text | ansi2html}}</pre>
</div>
{%- endblock pyout %}

{% block stream -%}
<div class="output_subarea output_stream output_stdout">
<pre>{{output.text |ansi2html}}</pre>
</div>
{%- endblock stream %}

{% block display_data -%}
<div class="output_subarea output_display_data">
{{output.svg}}
</div>
{%- endblock display_data %}


{% block pyerr -%}
<div class="output_subarea output_pyerr">
<pre>{{super()}}</pre>
</div>
{%- endblock pyerr %}

{%- block traceback_line %}
{{line| ansi2html}}
{%- endblock traceback_line %}
