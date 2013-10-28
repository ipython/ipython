{%- extends 'html_basic.tpl' -%}


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
</style>

<!-- Custom stylesheet, it must be in the same directory as the html file -->
<link rel="stylesheet" href="custom.css">

<script src="https://c328740.ssl.cf1.rackcdn.com/mathjax/latest/MathJax.js?config=TeX-AMS_HTML" type="text/javascript"></script>
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
<script type="text/javascript">
	var show_code = true
	function toggle_inputs() {
		var inputs = document.getElementsByClassName('input');
		if(show_code){
			for(var i=0; i<inputs.length; i++){inputs[i].style.display = "None"}
			show_code = false
		}
		else {
			for(var i=0; i<inputs.length; i++){inputs[i].style = "page-break-inside:avoid;display:-webkit-box;-webkit-box-orient:horizontal;-webkit-box-align:stretch;display:-moz-box;-moz-box-orient:horizontal;-moz-box-align:stretch;display:box;box-orient:horizontal;box-align:stretch;"}
			show_code = true
		};
	};
</script>
</head>
{%- endblock header -%}

{% block body %}
<body>
	<div id="body_div" style="display:block">

		<div style="
		float:left;
		height:100%;
		width:10%; 
		display:block;
		position: fixed;
		left: 1%;
		top: 10%;">
			<button onclick="toggle_inputs();">Show/Hide Input</button>
		</div>
	
		<div style="float:left; height:100%; width:88%; display:block; padding-left: 12%;">
			{{ super() }}
		</div>
	
	</div>
	

</body>
{%- endblock body %}

{% block footer %}
</html>
{% endblock footer %}
