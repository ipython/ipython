{%- extends 'basic.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}


{%- block header -%}
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8" />
<title>{{resources['metadata']['name']}}</title>

{% if resources.references.js is defined -%}
  {% for url in resources.references.js -%}
    <script src="{{ url }}"></script>
  {% endfor %}
{% endif %}

{% if resources.inlining.js is defined -%}
  {% for filename, js in resources.inlining.js -%}
    <!-- {{ filename }} -->
    <script>
      {{ js }}
    </script>
  {% endfor %}
{% endif %}

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
    <div class="container" id="notebook-container">

<script>

// Create widget models.
{% for model_id in nb.widgets -%}
IPython.widgets.create_widget("{{ model_id }}", "{{ nb.widgets[model_id].target }}"); 
{%- endfor %}

// Set widget model states.
{% for model_id in nb.widgets -%}
IPython.widgets.set_widget("{{ model_id }}", JSON.parse('{{ nb.widgets[model_id].state | tojson | replace("'", "\\'") }}')); 
{%- endfor %}

</script>

{{ super() }}

    </div>
  </div>
</body>
{%- endblock body %}

{% block footer %}
</html>
{% endblock footer %}

{%- block widget_group scoped -%}
<div class="widget-area">
<div class="prompt"><button class="close">&times;</button></div>
<div class="widget-subarea" id="widgetarea{{ worksheet.cells.index(cell) }}">
</div>
</div>

<script>
  // Display all of the widgets for this cell.
  {{ super() }}
</script>
{%- endblock widget_group -%}

{%- block widget scoped -%}
IPython.widgets.display_widget("{{ widget.id }}", "widgetarea{{ worksheet.cells.index(cell) }}"); 
{%- endblock widget -%}
