{%- extends 'html_basic.tpl' -%}

{% block header %}
<!-- Add this to your blog's template header if not already done. Do not add it to the blog post -->
<script type="application/javascript" src="https://google-code-prettify.googlecode.com/svn/loader/run_prettify.js"></script>
<script type="application/javascript" src="https://c328740.ssl.cf1.rackcdn.com/mathjax/latest/MathJax.js?config=TeX-AMS_HTML"></script>
<script type="application/javascript">
window.highlightAll = function() {
    // Use either google code prettifier or highlight.js
    if ( typeof(PR) != "undefined" ) {
	var segments = document.getElementsByTagName("pre");
        var elements = [];

	for(var i = 0; i < segments.length; i++) {
	    if( segments[i].firstChild.tagName === "CODE")
		elements.push(segments[i]);
	}

	for(var i = 0; i < elements.length; i++) {
	    var el = elements[i];
	    el.setAttribute("class", el.getAttribute("class")+" prettyprint");
	}	    
	PR.prettyPrint()
    }
}

window.mathjaxify = function() {
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
</script>

<!-- Add this to your blog's CSS template header if not already done. Do not add it to the blog post
     You might need to strip the enclosing <style> tags. -->
<style>
.notebook .input_area {  padding: 0.2em; }
.notebook pre {  padding: 0.2em;  border: none;  font-size: 13px;  background-color: rgb(255, 255, 255);  display: block;  font-family: monospace;  font-size: 13px;  line-height: 20px;  margin: 13PX 23px 13px 23px;  resize: none;  white-space: pre-wrap;  word-break: break-all;  word-wrap: break-word;}
.notebook pre.prettyprint {  border: none;}
.notebook h1,h2,h3,h4,h5,h6{margin:10px 0;font-family:inherit;font-weight:bold;line-height:20px;color:inherit;text-rendering:optimizelegibility;}h1 small,h2 small,h3 small,h4 small,h5 small,h6 small{font-weight:normal;line-height:1;color:#999999;}
.notebook h1,h2,h3{line-height:40px;}
.notebook h1{font-size:35.75px;}
.notebook h2{font-size:29.25px;}
.notebook h3{font-size:22.75px;}
.notebook h4{font-size:16.25px;}
.notebook h5{font-size:13px;}
.notebook h6{font-size:11.049999999999999px;}
.notebook h1 small{font-size:22.75px;}
.notebook h2 small{font-size:16.25px;}
.notebook h3 small{font-size:13px;}
.notebook h4 small{font-size:13px;}
.notebook ul,ol{padding:0;margin:0 0 10px 25px;}
.notebook ul ul,ul ol,ol ol,ol ul{margin-bottom:0;}
.notebook li{line-height:20px;}
.notebook div.cell{border:1px solid transparent;display:-webkit-box;-webkit-box-orient:vertical;-webkit-box-align:stretch;display:-moz-box;-moz-box-orient:vertical;-moz-box-align:stretch;display:box;box-orient:vertical;box-align:stretch;width:100%;padding:5px 5px 5px 0px;margin:2px 0px 2px 7px;outline:none;}
.notebook div.cell.selected{border-radius:4px;border:thin #ababab solid;}
.notebook div.prompt{float:left;width:11ex;padding:0.4em;margin:0px;font-family:monospace;text-align:right;line-height:1.231em;}
.notebook div.input{page-break-inside:avoid;}
.notebook div.input_area{border:1px solid #cfcfcf;border-radius:4px;background:#f7f7f7;overflow: hidden;width: auto; float: none;}
.notebook div.input_prompt{color:navy;border-top:1px solid transparent;}
.notebook div.output_wrapper{margin-top:5px;position:relative;display:-webkit-box;-webkit-box-orient:vertical;-webkit-box-align:stretch;display:-moz-box;-moz-box-orient:vertical;-moz-box-align:stretch;display:box;box-orient:vertical;box-align:stretch;width:100%;}
.notebook div.output_scroll{height:24em;width:100%;overflow:auto;border-radius:4px;-webkit-box-shadow:inset 0 2px 8px rgba(0, 0, 0, 0.8);-moz-box-shadow:inset 0 2px 8px rgba(0, 0, 0, 0.8);box-shadow:inset 0 2px 8px rgba(0, 0, 0, 0.8);}
.notebook div.output_collapsed{margin:0px;padding:0px;display:-webkit-box;-webkit-box-orient:vertical;-webkit-box-align:stretch;display:-moz-box;-moz-box-orient:vertical;-moz-box-align:stretch;display:box;box-orient:vertical;box-align:stretch;width:100%;}
.notebook div.out_prompt_overlay{height:100%;padding:0px 0.4em;position:absolute;border-radius:4px;}
.notebook div.out_prompt_overlay:hover{-webkit-box-shadow:inset 0 0 1px #000000;-moz-box-shadow:inset 0 0 1px #000000;box-shadow:inset 0 0 1px #000000;background:rgba(240, 240, 240, 0.5);}
.notebook div.output_prompt{color:darkred;}
.notebook .text_cell_render {text-align: justify;}
</style>
{%- endblock header %}


{% block footer %}
<!-- Add this to your blog's template FOOTER if not already done. Do not add it to the blog post -->
<script type="application/javascript">
window.mathjaxify();
window.highlightAll();
</script>
{% endblock footer %}


{% block body %}
<!-- Copy/paste this part into your blog post. -->
<div class="notebook">
{{ super() }}
</div>
{%- endblock body %}


{% block input %}
<div class="input_area box-flex1">
<pre class="prettyprint lang-{{ cell.language }}">
{{ cell.input | escape_for_html }}
</pre>
</div>
{%- endblock input %}

