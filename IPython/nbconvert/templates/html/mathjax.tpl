{%- macro mathjax() -%}
    <!-- MathJax configuration -->
    <script type="text/x-mathjax-config">
    MathJax.Hub.Config({
        tex2jax: {
            inlineMath: [ ['$','$'], ["\\(","\\)"] ],
            displayMath: [ ['$$','$$'], ["\\[","\\]"] ],
            processEscapes: true,
            processEnvironments: true
        },
        // Center justify equations in code and markdown cells. Elsewhere
        // we use CSS to left justify single line equations in code cells.
        displayAlign: 'center',
        "HTML-CSS": {
            styles: {'.MathJax_Display': {"margin": 0}},
            linebreaks: { automatic: true }
        }
    });
    </script>
    <!-- End of mathjax configuration -->

    <script>
    //  We wait for the onload function to load MathJax after the page is completely loaded.
    //  MathJax is loaded 1 unit of time after the page is ready.
    //  This hack prevent problems when you load multiple js files.

    window.onload = function () {
      setTimeout(function () {
        var script = document.createElement("script");
        script.type = "text/javascript";
        script.src  = "https://c328740.ssl.cf1.rackcdn.com/mathjax/latest/MathJax.js?config=TeX-AMS_HTML";
        document.getElementsByTagName("head")[0].appendChild(script);
      },1)
    }
    </script>
{%- endmacro %}