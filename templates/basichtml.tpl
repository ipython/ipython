{%- extends 'basic.tpl' -%}




{%  block codecell scoped  %}
<div class="cell border-box-sizing code_cell vbox">
<div class="input hbox">
<div class="prompt input_prompt">In&nbsp;[{{cell.prompt_number if cell.prompt_number else '&nbsp;'}}]:</div>
<div class="input_area box-flex1">
{{ cell.input|highlight -}}
</div>
</div>
{% if cell.outputs %}
{%- for output in cell.outputs -%}
<div class="vbox output_wrapper">
<div class="output vbox">
<div class="hbox output_area">
<div class="prompt output_prompt"></div>
    {%- if output.output_type in ['pyout','stream'] %}
<div class="output_subarea output_stream output_stdout">
<pre>{{ output.text }}</pre>
</div>
</div>
</div>
    {%- elif output.output_type in ['display_data'] %}
<div class="output_subarea output_display_data">
{{"# image file: fucking display_data"}}
</div>
    {%- elif output.output_type in ['pyerr'] %}
        {%- for line in output.traceback %}
{{ line |indent| rm_ansi}}
        {%- endfor %}
    {%- endif %}
{%- endfor -%}
{% endif %}
</div>
</div>
{% endblock codecell %}

{% block markdowncell scoped -%}
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
{{ cell.source | pycomment }}
{% endblock rawcell %}

{% block unknowncell scoped %}
unknown type  {{cell.type}}
{% endblock unknowncell %}
