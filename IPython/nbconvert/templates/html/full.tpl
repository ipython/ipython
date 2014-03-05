{%- extends 'basic.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}


{%- block header -%}
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8" />
<title>{{resources['metadata']['name']}}</title>

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
.input_area {
  padding: 0.2em;
}

pre {
  padding: 0.2em;
  border: none;
  margin: 0px;
  font-size: 13px;
}

div#notebook_panel {
  -webkit-box-shadow: none; 
  -moz-box-shadow: none; 
  box-shadow: none;
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
<div style="display: block;" id="site" class="border-box-sizing">
  <div id="ipython-main-app" class="border-box-sizing">
    <div id="notebook_panel" class="border-box-sizing">
      <div tabindex="-1" id="notebook" class="border-box-sizing">
        <div class="container" id="notebook-container">
{{ super() }}
        </div>
      </div>
    </div>
  </div>
</div>
</body>
{%- endblock body %}

{% block footer %}
</html>
{% endblock footer %}
