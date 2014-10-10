// IPython GFM (GitHub Flavored Markdown) mode is just a slightly altered GFM
// Mode with support for latex.
//
// Latex support was supported by Codemirror GFM as of
//   https://github.com/codemirror/CodeMirror/pull/567
// But was later removed in
//   https://github.com/codemirror/CodeMirror/commit/d9c9f1b1ffe984aee41307f3e927f80d1f23590c


(function(mod) {
  if (typeof exports == "object" && typeof module == "object"){ // CommonJS
    mod(require("codemirror/lib/codemirror")
        ,require("codemirror/addon/mode/multiplex")
        ,require("codemirror/mode/gfm/gfm")
        ,require("codemirror/mode/stex/stex")
        );
  } else if (typeof define == "function" && define.amd){ // AMD
    define(["codemirror/lib/codemirror"
            ,"codemirror/addon/mode/multiplex"
            ,"codemirror/mode/python/python"
            ,"codemirror/mode/stex/stex"
            ], mod);
  } else {// Plain browser env
    mod(CodeMirror);
  }
})( function(CodeMirror){
    "use strict";

    CodeMirror.defineMode("ipythongfm", function(config, parserConfig) {

        var gfm_mode = CodeMirror.getMode(config, "gfm");
        var tex_mode = CodeMirror.getMode(config, "stex");

        return CodeMirror.multiplexingMode(
            gfm_mode,
            {
                open: "$", close: "$",
                mode: tex_mode,
                delimStyle: "delimit"
            },
            {
                // not sure this works as $$ is interpreted at (opening $, closing $, as defined just above)
                open: "$$", close: "$$",
                mode: tex_mode,
                delimStyle: "delimit"
            },
            {
                open: "\\(", close: "\\)",
                mode: tex_mode,
                delimStyle: "delimit"
            },
            {
                open: "\\[", close: "\\]",
                mode: tex_mode,
                delimStyle: "delimit"
            }
            // .. more multiplexed styles can follow here
        );
    }, 'gfm');

    CodeMirror.defineMIME("text/x-ipythongfm", "ipythongfm");
})
