{%- extends 'slides.tpl' -%}


{% block header %}
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8" />
<meta http-equiv="X-UA-Compatible" content="chrome=1">

<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />

<link rel="stylesheet" href="reveal.js/css/reveal.css">
<link rel="stylesheet" href="reveal.js/css/theme/simple.css" id="theme">

<!-- For syntax highlighting -->
<link rel="stylesheet" href="reveal.js/lib/css/zenburn.css">

<!-- If the query includes 'print-pdf', use the PDF print sheet -->
<script>
document.write( '<link rel="stylesheet" href="reveal.js/css/print/' + ( window.location.search.match( /print-pdf/gi ) ? 'pdf' : 'paper' ) + '.css" type="text/css" media="print">' );
</script>

<!--[if lt IE 9]>
<script src="reveal.js/lib/js/html5shiv.js"></script>
<![endif]-->

{% for css in resources.inlining.css -%}
<style type="text/css">
{{css}}
</style>
{% endfor %}

<style type="text/css">
/* Overrides of notebook CSS for static HTML export */
.reveal {
font-size: 20px;
overflow-y: auto;
overflow-x: hidden;
}
.reveal pre {
width: 95%;
padding: 0.4em;
margin: 0px;
font-family: monospace, sans-serif;
font-size: 80%;
box-shadow: 0px 0px 0px rgba(0, 0, 0, 0);
}
.reveal section img {
border: 0px solid black;
box-shadow: 0 0 10px rgba(0, 0, 0, 0);
}
.reveal .slides {
text-align: left;
}
.reveal.fade {
opacity: 1;
}
div.input_area {
padding: 0.06em;
}
div.code_cell {
background-color: transparent;
}
div.prompt {
width: 11ex;
padding: 0.4em;
margin: 0px;
font-family: monospace, sans-serif;
font-size: 80%;
text-align: right;
}
div.output_area pre {
font-family: monospace, sans-serif;
font-size: 80%;
}
div.output_prompt {
    /* 5px right shift to account for margin in parent container */
    margin: 5px 5px 0 -5px;
}
.rendered_html p {
text-align: inherit;
}
</style>
</head>
{% endblock header%}


{% block body %}
<body>
<div class="reveal"><div class="slides">

{{ super() }}

</div></div>

<!-- 
Uncomment the following block and the addthis_widget.js (see below inside dependencies)
to get enable social buttons.
-->

<!--
<div class="addthis_toolbox addthis_floating_style addthis_32x32_style" style="left:20px;top:20px;">
<a class="addthis_button_twitter"></a>
<a class="addthis_button_google_plusone_share"></a>
<a class="addthis_button_linkedin"></a>
<a class="addthis_button_facebook"></a>
<a class="addthis_button_more"></a>
</div>
-->

<script src="reveal.js/lib/js/head.min.js"></script>

<script src="reveal.js/js/reveal.min.js"></script>

<script>

// Full list of configuration options available here: https://github.com/hakimel/reveal.js#configuration
Reveal.initialize({
controls: true,
progress: true,
history: true,

theme: Reveal.getQueryHash().theme, // available themes are in /css/theme
transition: Reveal.getQueryHash().transition || 'linear', // default/cube/page/concave/zoom/linear/none

// Optional libraries used to extend on reveal.js
dependencies: [
{ src: 'reveal.js/lib/js/classList.js', condition: function() { return !document.body.classList; } },
{ src: 'reveal.js/plugin/highlight/highlight.js', async: true, callback: function() { hljs.initHighlightingOnLoad(); } },
{ src: 'reveal.js/plugin/notes/notes.js', async: true, condition: function() { return !!document.body.classList; } }
// { src: 'http://s7.addthis.com/js/300/addthis_widget.js', async: true},
]
});
</script>

<!-- MathJax configuration -->
<script type="text/x-mathjax-config">
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
</script>
<!-- End of mathjax configuration -->

<script>
//  We wait for the onload function to load MathJax after the page is completely loaded.  
//  MathJax is loaded 1 unit of time after the page is ready.
//  This hack prevent problems when you load multiple js files (i.e. social button from addthis).
//
window.onload = function () {
  setTimeout(function () {
    var script = document.createElement("script");
    script.type = "text/javascript";
    script.src  = "https://c328740.ssl.cf1.rackcdn.com/mathjax/latest/MathJax.js?config=TeX-AMS_HTML";
    document.getElementsByTagName("head")[0].appendChild(script);
  },1)
}
</script>

<script>
Reveal.addEventListener( 'slidechanged', function( event ) {
MathJax.Hub.Rerender(event.currentSlide);
});
</script>

</body>
{% endblock body %}

{% block footer %}
</html>
{% endblock footer %}
