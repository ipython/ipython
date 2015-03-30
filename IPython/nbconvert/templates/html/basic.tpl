{%- extends 'display_priority.tpl' -%}


{% block codecell %}
<div class="cell border-box-sizing code_cell rendered">
{{ super() }}
</div>
{%- endblock codecell %}

{% block input_group -%}
<div class="input">
{{ super() }}
</div>
{% endblock input_group %}

{% block output_group %}
<div class="output_wrapper">
<div class="output">
{{ super() }}
</div>
</div>
{% endblock output_group %}

{% block in_prompt -%}
<div class="prompt input_prompt">
{%- if cell.execution_count is defined -%}
In&nbsp;[{{ cell.execution_count|replace(None, "&nbsp;") }}]:
{%- else -%}
In&nbsp;[&nbsp;]:
{%- endif -%}
</div>
{%- endblock in_prompt %}

{% block empty_in_prompt -%}
<div class="prompt input_prompt">
</div>
{%- endblock empty_in_prompt %}

{# 
  output_prompt doesn't do anything in HTML,
  because there is a prompt div in each output area (see output block)
#}
{% block output_prompt %}
{% endblock output_prompt %}

{% block input %}
<div class="inner_cell">
    <div class="input_area">
{{ cell.source | highlight_code(metadata=cell.metadata) }}
</div>
</div>
{%- endblock input %}

{% block output %}
<div class="output_area">
{%- if output.output_type == 'execute_result' -%}
    <div class="prompt output_prompt">
{%- if cell.execution_count is defined -%}
    Out[{{ cell.execution_count|replace(None, "&nbsp;") }}]:
{%- else -%}
    Out[&nbsp;]:
{%- endif -%}
{%- else -%}
    <div class="prompt">
{%- endif -%}
    </div>
{{ super() }}
</div>
{% endblock output %}

{% block markdowncell scoped %}
<div class="cell border-box-sizing text_cell rendered">
{{ self.empty_in_prompt() }}
<div class="inner_cell">
<div class="text_cell_render border-box-sizing rendered_html">
{{ cell.source  | markdown2html | strip_files_prefix }}
</div>
</div>
</div>
{%- endblock markdowncell %}

{% block unknowncell scoped %}
unknown type  {{ cell.type }}
{% endblock unknowncell %}

{% block execute_result -%}
{%- set extra_class="output_execute_result" -%}
{% block data_priority scoped %}
{{ super() }}
{% endblock %}
{%- set extra_class="" -%}
{%- endblock execute_result %}

{% block stream_stdout -%}
<div class="output_subarea output_stream output_stdout output_text">
<pre>
{{- output.text | ansi2html -}}
</pre>
</div>
{%- endblock stream_stdout %}

{% block stream_stderr -%}
<div class="output_subarea output_stream output_stderr output_text">
<pre>
{{- output.text | ansi2html -}}
</pre>
</div>
{%- endblock stream_stderr %}

{% block data_svg scoped -%}
<div class="output_svg output_subarea {{extra_class}}">
{%- if output.svg_filename %}
<img src="{{output.svg_filename | posix_path}}"
{%- else %}
{{ output.data['image/svg+xml'] }}
{%- endif %}
</div>
{%- endblock data_svg %}

{% block data_html scoped -%}
<div class="output_html rendered_html output_subarea {{extra_class}}">
{{ output.data['text/html'] }}
</div>
{%- endblock data_html %}

{% block data_markdown scoped -%}
<div class="output_markdown rendered_html output_subarea {{extra_class}}">
{{ output.data['text/markdown'] | markdown2html }}
</div>
{%- endblock data_markdown %}

{% block data_png scoped %}
<div class="output_png output_subarea {{extra_class}}">
{%- if 'image/png' in output.metadata.get('filenames', {}) %}
<img src="{{output.metadata.filenames['image/png'] | posix_path}}"
{%- else %}
<img src="data:image/png;base64,{{ output.data['image/png'] }}"
{%- endif %}
{%- if 'width' in output.metadata.get('image/png', {}) %}
width={{output.metadata['image/png']['width']}}
{%- endif %}
{%- if 'height' in output.metadata.get('image/png', {}) %}
height={{output.metadata['image/png']['height']}}
{%- endif %}
{%- if output.metadata.get('image/png', {}).get('unconfined') %}
class="unconfined"
{%- endif %}
>
</div>
{%- endblock data_png %}

{% block data_jpg scoped %}
<div class="output_jpeg output_subarea {{extra_class}}">
{%- if 'image/jpeg' in output.metadata.get('filenames', {}) %}
<img src="{{output.metadata.filenames['image/jpeg'] | posix_path}}"
{%- else %}
<img src="data:image/jpeg;base64,{{ output.data['image/jpeg'] }}"
{%- endif %}
{%- if 'width' in output.metadata.get('image/jpeg', {}) %}
width={{output.metadata['image/jpeg']['width']}}
{%- endif %}
{%- if 'height' in output.metadata.get('image/jpeg', {}) %}
height={{output.metadata['image/jpeg']['height']}}
{%- endif %}
>
</div>
{%- endblock data_jpg %}

{% block data_latex scoped %}
<div class="output_latex output_subarea {{extra_class}}">
{{ output.data['text/latex'] }}
</div>
{%- endblock data_latex %}

{% block error -%}
<div class="output_subarea output_text output_error">
<pre>
{{- super() -}}
</pre>
</div>
{%- endblock error %}

{%- block traceback_line %}
{{ line | ansi2html }}
{%- endblock traceback_line %}

{%- block data_text scoped %}
<div class="output_text output_subarea {{extra_class}}">
<pre>
{{- output.data['text/plain'] | ansi2html -}}
</pre>
</div>
{%- endblock -%}

{%- block data_javascript scoped %}
<div class="output_subarea output_javascript {{extra_class}}">
<script type="text/javascript">
{{ output.data['application/javascript'] }}
</script>
</div>
{%- endblock -%}
