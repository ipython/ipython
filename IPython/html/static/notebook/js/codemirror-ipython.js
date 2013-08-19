// IPython mode is just a slightly altered Python Mode with `?` beeing a extra
// single operator. Here we define `ipython` mode in the require `python`
// callback to auto-load python mode, which is more likely not the best things
// to do, but at least the simple one for now.

CodeMirror.requireMode('python',function(){
    "use strict";

    CodeMirror.defineMode("ipython", function(conf, parserConf) {

        parserConf.singleOperators = new RegExp("^[\\+\\-\\*/%&|\\^~<>!\\?]");
        parserConf.name = 'python'
        return CodeMirror.getMode(conf, parserConf);
    }, 'python');

    CodeMirror.defineMIME("text/x-ipython", "ipython");
})
