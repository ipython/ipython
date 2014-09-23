// IPython GFM (GitHub Flavored Markdown) mode is just a slightly altered GFM 
// Mode with support for latex. 
//
// Latex support was supported by Codemirror GFM as of 
//   https://github.com/codemirror/CodeMirror/pull/567
// But was later removed in
//   https://github.com/codemirror/CodeMirror/commit/d9c9f1b1ffe984aee41307f3e927f80d1f23590c

CodeMirror.requireMode('gfm', function(){ 
    CodeMirror.requireMode('stex', function(){ 
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
    });
});
