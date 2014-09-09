// IPython mode is just a slightly altered Python Mode with `?` beeing a extra
// single operator. Here we define `ipython` mode in the require `python`
// callback to auto-load python mode, which is more likely not the best things
// to do, but at least the simple one for now.

CodeMirror.requireMode('python',function(){
    "use strict";

    CodeMirror.defineMode("ipython", function(conf, parserConf) {
        var pythonConf = {};
        for (var prop in parserConf) {
            if (parserConf.hasOwnProperty(prop)) {
                pythonConf[prop] = parserConf[prop];
            }
        }
        pythonConf.name = 'python';
        pythonConf.singleOperators = new RegExp("^[\\+\\-\\*/%&|\\^~<>!\\?]");
        if (pythonConf.version === 3) {
            pythonConf.identifiers = new RegExp("^[_A-Za-z\u00A1-\uFFFF][_A-Za-z0-9\u00A1-\uFFFF]*");
        } else if (pythonConf.version === 2) {
            pythonConf.identifiers = new RegExp("^[_A-Za-z][_A-Za-z0-9]*");
        }
        return CodeMirror.getMode(conf, pythonConf);
    }, 'python');

    CodeMirror.defineMIME("text/x-ipython", "ipython");
})
