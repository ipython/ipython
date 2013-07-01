{%- extends 'basichtml.tpl' -%}

{%- block header -%}<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>[{{nb.metadata.name}}]</title>
{% for css in resources.inlining.css -%}
<style type="text/css">
{{css}}
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
    border: none;
    margin: 0px;
    font-size: 13px;
}
</style>

<script src="https://c328740.ssl.cf1.rackcdn.com/mathjax/latest/MathJax.js?config=TeX-AMS_HTML" type="text/javascript">

</script>
<script type="text/javascript">
init_mathjax = function() {
    if (window.MathJax) {
        // MathJax loaded
        MathJax.Hub.Config({
            tex2jax: {
                inlineMath: [ ['$','$'], ["\\(","\\)"] ],
                displayMath: [ ['$$','$$'], ["\\[","\\]"] ]
            },
            displayAlign: 'left', // Change this to 'center' to center equations.
            "HTML-CSS": {
                styles: {'.MathJax_Display': {"margin": 0}}
            }
        });
        MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
    }
}
init_mathjax();
</script>
</head>
{%- endblock header -%}


{% block body %}
<body>{{ super() }}
</body>
{%- endblock body %}


{% block footer %}
</html>{% endblock footer %}
