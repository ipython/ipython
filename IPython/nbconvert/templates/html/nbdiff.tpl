{%- extends 'basic.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}


{%- block header -%}
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8" />
<title>{{resources['metadata']['name']}} - {{ resources['left']['name'] }} <> {{ resources['right']['name'] }}</title>

<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>

<script>
function hideOutput(hide){
    if (hide){
        $(".output_wrapper").hide();
        $("#toggle_output").text("+ Show Outputs");
        $("#toggle_output").unbind('click').click(function(){hideOutput(false)});
    } else {
        $(".output_wrapper").show();
        $("#toggle_output").text("- Hide Outputs");
        $("#toggle_output").unbind('click').click(function(){hideOutput(true)});
    }
};
$(document).ready(function() {
    hideOutput(false);
});
</script>

{% for css in resources.inlining.css -%}
    <style type="text/css">
    {{ css }}
    </style>
{% endfor %}

<style type="text/css">
/* Overrides of notebook CSS for static HTML export */
body {
  overflow: visible;
  padding: 8px;
}

div#notebook {
  overflow: visible;
  border-top: none;
}

@media print {
  div.cell {
    display: block;
    page-break-inside: avoid;
  } 
  div.output_wrapper { 
    display: block;
    page-break-inside: avoid; 
  }
  div.output { 
    display: block;
    page-break-inside: avoid; 
  }
}

div.nbdiff {
  margin-bottom:40px;
  width:80%;
  margin:auto;
}

div.nbdiff .nbdiff_panel {
  border:1px solid black;
  border-radius:8px;
  padding:10px;
}

.rendered_html *+div>p {
  margin-top:1em;
}

div.cell_state.deleted,
.source_state.deleted,
div.nbdiff .left,
div.input_state.deleted pre,
div.output_state.deleted > .output_area {
  background-color:#FFBBBB
}

div.cell_state.added,
.source_state.added,
div.nbdiff .right,
div.input_state.added pre,
div.output_state.added > .output_area {
  background-color:#BBFFBB
}

.cell_state.modified {
  background-color:#FFFFDD
}

div.input_state pre {
  padding:0;
  border:0;
  margin:0;
  background-color:transparent;
}
</style>

<!-- Custom stylesheet, it must be in the same directory as the html file -->
<link rel="stylesheet" href="custom.css">

<!-- Loading mathjax macro -->
{{ mathjax() }}

</head>
{%- endblock header -%}

{% block body %}
<body>
  <div tabindex="-1" id="notebook" class="border-box-sizing">
    <div class="container"><div class="nbdiff">
      <h1><span class="left">{{ resources['left']['name'] }}</span> <> <span class="right">{{ resources['right']['name'] }}</span></h1>
      <div class="nbdiff_panel">
        <h3>Diff List</h3><ul>
          {% for cell in nb['cells'] %}
            {% if cell['metadata']['state'] != "unchanged" %}
            <li><a href="#{{ cell['metadata']['id'] }}">{{ cell['metadata']['id'] }} ({{ cell['metadata']['state'] }})</a></li>
            {% endif %}
          {% endfor %}
        </ul>
        <button id="toggle_output" class="btn"></button>
      </div>
    </div></div>
    <hr />
    <div class="container" id="notebook-container">
      {{ super() }}
    </div>
  </div>
</body>
{%- endblock body %}

{% block footer %}
</html>
{% endblock footer %}

{% block any_cell %}
<div id="{{ cell.metadata.id }}" class="cell_state {{ cell.metadata.state }}">
{{ super() }}
</div>
{%- endblock any_cell %}

{%- block codecell -%}
<div class="cell border-box-sizing code_cell rendered">
{%- block input_group -%}
{{ super() }}
{%- endblock input_group -%}
{%- block output_group -%}
{{ super() }}
{%- endblock output_group -%}
</div>
{%- endblock codecell -%}

{% block input %}
<div class="inner_cell">
    <div class="input_area">
    {% if "extra-diff-data" in cell.metadata and "source" in cell.metadata['extra-diff-data'] %}
        <div class="highlight">
        {% for source in cell.metadata['extra-diff-data'].source %}
            <div class="input_state {{source.state}}">
            {{ source.value | highlight_code(metadata=cell.metadata) }}
            </div>
        {% endfor %}
        </div>
    {% else %}
        {{ cell.source | highlight_code(metadata=cell.metadata) }}
    {% endif %}
</div>
</div>
{%- endblock input %}

{% block outputs %}
{% if "extra-diff-data" in cell.metadata and "outputs" in cell.metadata['extra-diff-data'] %}
    {% for output in cell.metadata['extra-diff-data'].outputs %}
        <div class="output_state {{output.state}}">
            {% set output = output.value %}
            {% block output scoped %}
            {{ super() }}
            {% endblock output %}
        </div>
    {% endfor %}
{% else %}
    {{ super() }}
{% endif %}
{% endblock outputs %}

{% block markdowncell scoped %}
<div class="cell border-box-sizing text_cell rendered">
{{ self.empty_in_prompt() }}
<div class="inner_cell">
<div class="text_cell_render border-box-sizing rendered_html">
{% if "extra-diff-data" in cell.metadata and "source" in cell.metadata['extra-diff-data'] %}
  {% for source in cell.metadata['extra-diff-data'].source %}
  <div class="source_state {{ source.state }}">
  {{ source.value | markdown2html | strip_files_prefix }}
  </div>
  {% endfor %}
{% else %}
{{ cell.source  | markdown2html | strip_files_prefix }}
{% endif %}
</div>
</div>
</div>
{%- endblock markdowncell %}

{%- block rawcell scoped -%}
{% if cell.metadata.get('raw_mimetype', '').lower() in resources.get('raw_mimetypes', ['']) %}
{% if "extra-diff-data" in cell.metadata and "source" in cell.metadata['extra-diff-data'] %}
{% for source in cell.metadata['extra-diff-data'].source %}
<span class="source_state {{ source.state }}">
{{ source.value }}
</span>
{% endfor %}
{% else %}
{{ cell.source }}
{% endif %}
{% endif %}
{%- endblock rawcell -%}