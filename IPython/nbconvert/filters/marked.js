// Node.js script for markdown to html conversion
// This applies the same math extraction and marked settings
// that we use in the live notebook.

// IPython static_path dir relative to here:
var static_path = __dirname + "/../../html/static/";

var fs = require('fs');
var IPython;
// marked can be loaded with require,
// the others must be execfiled
var marked = require(static_path + 'components/marked/lib/marked.js');

eval(fs.readFileSync(static_path + "components/highlight.js/build/highlight.pack.js", 'utf8'));
eval(fs.readFileSync(static_path + "base/js/namespace.js", 'utf8'));

eval(fs.readFileSync(static_path + "base/js/utils.js", 'utf8'));
eval(fs.readFileSync(static_path + "notebook/js/mathjaxutils.js", 'utf8'));

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
    var text_and_math = IPython.mathjaxutils.remove_math(md);
    var text = text_and_math[0];
    var math = text_and_math[1];
    var html = marked.parser(marked.lexer(text));
    html = IPython.mathjaxutils.replace_math(html, math);
    process.stdout.write(html);
});
