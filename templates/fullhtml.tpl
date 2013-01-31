{%- extends 'basichtml.tpl' -%}

{%- block header -%}<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>[{{nb.metadata.name}}]</title>
{% for css in inlining.css -%}
<style type="text/css">
{{css}}
</style>
{% endfor %}
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
