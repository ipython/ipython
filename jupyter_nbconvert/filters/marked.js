// Node.js script for markdown to html conversion
// This applies the same math extraction and marked settings
// that we use in the live notebook.

// IPython static_path dir relative to here:
var static_path = __dirname + "/../../html/static/";

// Excerpt from the example in require.js docs
// http://requirejs.org/docs/node.html
var requirejs = require('requirejs');
requirejs.config({
    //Pass the top-level main.js/index.js require
    //function to requirejs so that node modules
    //are loaded relative to the top-level JS file.
    nodeRequire: require,
    baseUrl: static_path,
});

requirejs([
    'fs',
    'components/marked/lib/marked',
    'components/highlight.js/build/highlight.pack',
    'base/js/utils',
    'notebook/js/mathjaxutils',
    ], function(fs, marked, hljs, utils, mathjaxutils) {

    // this is copied from notebook.main. Should it be moved somewhere we can reuse it?
    marked.setOptions({
        gfm : true,
        tables: true,
        langPrefix: "language-",
        highlight: function(code, lang) {
            if (!lang) {
                // no language, no highlight
                return code;
            }
            var highlighted;
            try {
                highlighted = hljs.highlight(lang, code, false);
            } catch(err) {
                highlighted = hljs.highlightAuto(code);
            }
            return highlighted.value;
        }
    });

    // read the markdown from stdin
    var md='';
    process.stdin.on("data", function (data) {
        md += data;
    });

    // perform the md2html transform once stdin is complete
    process.stdin.on("end", function () {
        var text_and_math = mathjaxutils.remove_math(md);
        var text = text_and_math[0];
        var math = text_and_math[1];
        var html = marked.parser(marked.lexer(text));
        html = mathjaxutils.replace_math(html, math);
        process.stdout.write(html);
    });

});
