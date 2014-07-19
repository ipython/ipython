{%- extends 'basic.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}

{%- block any_cell scoped -%}

{% macro slide_opts(cell) -%}
{# examines a slide cell's metadata for reveal.js formatting options #}
    {%- if cell.metadata.slideshow.slide_background -%}
        {{" "}}data-background="{{ cell.metadata.slideshow.slide_background }}"
    {%- endif -%}

    {%- if cell.metadata.slideshow.slide_background_repeat -%}
        {{" "}}data-background-repeat="{{ cell.metadata.slideshow.slide_background_repeat }}"
    {%- endif -%}

    {%- if cell.metadata.slideshow.slide_background_size -%}
        {{" "}}data-background-size="{{ cell.metadata.slideshow.slide_background_size }}"
    {%- endif -%}
    
    {%- if cell.metadata.slideshow.slide_background_transition -%}
        {{" "}}data-background-transition="{{ cell.metadata.slideshow.slide_background_transition }}"
    {%- endif -%}

    {%- if cell.metadata.slideshow.slide_transition -%}
        {{" "}}data-transition="{{ cell.metadata.slideshow.slide_transition }}"
    {%- endif -%}

    {%- if cell.metadata.slideshow.slide_transition_speed -%}
        {{" "}}data-transition-speed="{{ cell.metadata.slideshow.slide_transition_speed }}"
    {%- endif -%}
{%- endmacro %}

{%- macro fragment_style(cell) -%}
{# examines a fragment cell's metadata for reveal.js fragment highlight style option.
"higlight-red", "highlight-blue" and "higlight-green" not supported #}
    {%- if cell.metadata.slideshow.fragment_style -%}
        {{" "+cell.metadata.slideshow.fragment_style}}
    {%- endif -%}
{%- endmacro %}

{%- if cell.metadata.slide_type in ['slide'] -%}
    <section>
    <section {{ slide_opts(cell) }}>

    {{ super() }}
{%- elif cell.metadata.slide_type in ['subslide'] -%}
    <section {{ slide_opts(cell) }}>
    {{ super() }}
{%- elif cell.metadata.slide_type in ['-'] -%}
    {%- if cell.metadata.frag_helper in ['fragment_end'] -%}
        <div class="fragment{{ fragment_style(cell) }}" data-fragment-index="{{ cell.metadata.frag_number }}">
        {{ super() }}
        </div>
    {%- else -%}
        {{ super() }}
    {%- endif -%}
{%- elif cell.metadata.slide_type in ['skip'] -%}
    <div style=display:none>
    {{ super() }}
    </div>
{%- elif cell.metadata.slide_type in ['notes'] -%}
    <aside class="notes">
    {{ super() }}
    </aside>
{%- elif cell.metadata.slide_type in ['fragment'] -%}
    <div class="fragment{{ fragment_style(cell) }}" data-fragment-index="{{ cell.metadata.frag_number }}">
    {{ super() }}
    </div>
{%- endif -%}
{%- if cell.metadata.slide_helper in ['subslide_end'] -%}
    </section>
{%- elif cell.metadata.slide_helper in ['slide_end'] -%}
    </section>
    </section>
{%- endif -%}
{%- endblock any_cell -%}

{% block header %}
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8" />
<meta http-equiv="X-UA-Compatible" content="chrome=1" />

<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />

<title>{{resources['metadata']['name']}} slides</title>

<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>

<!-- General and theme style sheets -->
<link rel="stylesheet" href="{{resources.reveal.url_prefix}}/css/reveal.css">
<link rel="stylesheet" href="{{resources.reveal.url_prefix}}/css/theme/simple.css" id="theme">

<!-- For syntax highlighting -->
<link rel="stylesheet" href="{{resources.reveal.url_prefix}}/lib/css/zenburn.css">

<!-- If the query includes 'print-pdf', include the PDF print sheet -->
<script>
if( window.location.search.match( /print-pdf/gi ) ) {
        var link = document.createElement( 'link' );
        link.rel = 'stylesheet';
        link.type = 'text/css';
        link.href = '{{resources.reveal.url_prefix}}/css/print/pdf.css';
        document.getElementsByTagName( 'head' )[0].appendChild( link );
}

</script>

<!--[if lt IE 9]>
<script src="{{resources.reveal.url_prefix}}/lib/js/html5shiv.js"></script>
<![endif]-->

<!-- Get Font-awesome from cdn -->
<link rel="stylesheet" href="//netdna.bootstrapcdn.com/font-awesome/3.2.1/css/font-awesome.css">

{% for css in resources.inlining.css -%}
    <style type="text/css">
    {{ css }}
    </style>
{% endfor %}

<style type="text/css">
/* Overrides of notebook CSS for static HTML export */
html {
  overflow-y: auto;
}
.reveal {
  font-size: 160%;
}
.reveal pre {
  width: inherit;
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
.reveal i {
  font-style: normal;
  font-family: FontAwesome;
  font-size: 2em;
}
.reveal .slides {
  text-align: left;
}
.reveal.fade {
  opacity: 1;
}
.reveal .progress {
  position: static;
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
  margin: 5px 5px 0 0;
}
.rendered_html p {
  text-align: inherit;
}
</style>

<!-- Custom stylesheet, it must be in the same directory as the html file -->
<link rel="stylesheet" href="custom.css">

</head>
{% endblock header%}


{% block body %}
<body>
<div class="reveal">
<div class="slides">
{{ super() }}
</div>
</div>

<script src="{{resources.reveal.url_prefix}}/lib/js/head.min.js"></script>

<script src="{{resources.reveal.url_prefix}}/js/reveal.js"></script>

<script>

// Full list of configuration options available here: https://github.com/hakimel/reveal.js#configuration
Reveal.initialize({

    {%- if nb.metadata.slideshow.controls in ['true', 'false'] -%}
        controls: {{ nb.metadata.slideshow.controls }},
    {%- else -%}
        controls: true,
    {%- endif -%}

    {%- if nb.metadata.slideshow.progress in ['true', 'false'] -%}
        progress: {{ nb.metadata.slideshow.progress }},
    {%- else -%}
        progress: true,
    {%- endif -%}

    {%- if nb.metadata.slideshow.history in ['true', 'false'] -%}
        history: {{ nb.metadata.slideshow.history }},
    {%- else -%}
        history: true,
    {%- endif -%}
    
    {%- if nb.metadata.slideshow.slide_number in ['true', 'false'] -%}
        slideNumber: {{ nb.metadata.slideshow.slide_number }},
    {%- endif -%}
    
    {%- if nb.metadata.slideshow.keyboard in ['true', 'false'] -%}
        keyboard: {{ nb.metadata.slideshow.keyboard }},
    {%- endif -%}
    
    {%- if nb.metadata.slideshow.overview in ['true', 'false'] -%}
        overview: {{ nb.metadata.slideshow.overview }},
    {%- endif -%}
    
    {%- if nb.metadata.slideshow.center in ['true', 'false'] -%}
        center: {{ nb.metadata.slideshow.center }},
    {%- endif -%}
    
    {%- if nb.metadata.slideshow.touch in ['true', 'false'] -%}
        touch: {{ nb.metadata.slideshow.touch }},
    {%- endif -%}
    
    {%- if nb.metadata.slideshow.loop in ['true', 'false'] -%}
        loop: {{ nb.metadata.slideshow.loop }},
    {%- endif -%}

    {%- if nb.metadata.slideshow.rtl in ['true', 'false'] -%}
        rtl: {{ nb.metadata.slideshow.rtl }},
    {%- endif -%}

    {%- if nb.metadata.slideshow.fragments in ['true', 'false'] -%}
        fragments: {{ nb.metadata.slideshow.fragments }},
    {%- endif -%}

    {%- if nb.metadata.slideshow.embedded in ['true', 'false'] -%}
        embedded: {{ nb.metadata.slideshow.embedded }},
    {%- endif -%}
    
    {%- if nb.metadata.slideshow.auto_slide -%}
        autoSlide: {{ nb.metadata.slideshow.auto_slide }},
    {%- endif -%}
    
    {%- if nb.metadata.slideshow.auto_slide_stoppable in ['true', 'false'] -%}
        autoSlideStoppable: {{ nb.metadata.slideshow.auto_slide_stoppable }},
    {%- endif -%}

    {%- if nb.metadata.slideshow.mouse_wheel in ['true', 'false'] -%}
        mouseWheel: {{ nb.metadata.slideshow.mouse_wheel }},
    {%- endif -%}
    
    {%- if nb.metadata.slideshow.hide_address_bar in ['true', 'false'] -%}
        hideAddressBar: {{ nb.metadata.slideshow.hide_address_bar }},
    {%- endif -%}
    
    {%- if nb.metadata.slideshow.preview_links in ['true', 'false'] -%}
        previewLinks: {{ nb.metadata.slideshow.preview_links }},
    {%- endif -%}

    {%- if nb.metadata.slideshow.transition in ['default', 'cube', 'page', 'concave', 'zoom', 'linear', 'fade', 'none'] -%}
        transition: {{ nb.metadata.slideshow.transition }},
    {%- else -%}
        transition: Reveal.getQueryHash().transition || 'linear',
    {%- endif -%}

    {%- if nb.metadata.slideshow.transition_speed in ['default', 'fast', 'slow'] -%}
        transitionSpeed: {{ nb.metadata.slideshow.transition_speed }},
    {%- endif -%}

    {%- if nb.metadata.slideshow.background_transition in ['default', 'none', 'slide', 'concave', 'convex', 'zoom'] -%}
        transition: {{ nb.metadata.slideshow.background_transition  }},
    {%- endif -%}

    {%- if nb.metadata.slideshow.view_distance in ['default', 'none', 'slide', 'concave', 'convex', 'zoom'] -%}
        viewDistance: {{ nb.metadata.slideshow.view_distance }},
    {%- endif -%}

    {%- if nb.metadata.slideshow.parallax_background_image -%}
        parallaxBackgroundImage: {{ nb.metadata.slideshow.parallax_background_image }},
    {%- endif -%}


    {%- if nb.metadata.slideshow.parallax_background_size -%}
        parallaxBackgroundSize: {{ nb.metadata.slideshow.parallax_background_size }},
    {%- endif -%}


theme: Reveal.getQueryHash().theme, // available themes are in /css/theme

// Optional libraries used to extend on reveal.js
dependencies: [
{ src: "{{resources.reveal.url_prefix}}/lib/js/classList.js", condition: function() { return !document.body.classList; } },
{ src: "{{resources.reveal.url_prefix}}/plugin/notes/notes.js", async: true, condition: function() { return !!document.body.classList; } }
]
});
</script>

<!-- Loading mathjax macro -->
{{ mathjax() }}

<script>
Reveal.addEventListener( 'slidechanged', function( event ) {
  window.scrollTo(0,0);
  MathJax.Hub.Rerender(event.currentSlide);
});
</script>

</body>
{% endblock body %}

{% block footer %}
</html>
{% endblock footer %}