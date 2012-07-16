=======================
 CodeMirror in IPython
=======================

We carry a mostly unmodified copy of CodeMirror.  The current version we use
is (*please update this information when updating versions*)::

  CodeMirror c813c94

The only changes we've applied so far are these::

    diff --git a/IPython/frontend/html/notebook/static/codemirror/mode/python/python.js b/IPython/frontend/html/notebook/static/codemirror/mode/python/python.js
    index ca94e7a..fc9a503 100644
    --- a/IPython/frontend/html/notebook/static/codemirror/mode/python/python.js
    +++ b/IPython/frontend/html/notebook/static/codemirror/mode/python/python.js
    @@ -5,7 +5,11 @@ CodeMirror.defineMode("python", function(conf, parserConf) {
	     return new RegExp("^((" + words.join(")|(") + "))\\b");
	 }

    -    var singleOperators = new RegExp("^[\\+\\-\\*/%&|\\^~<>!]");
    +    // IPython-specific changes: add '?' as recognized character.
    +    //var singleOperators = new RegExp("^[\\+\\-\\*/%&|\\^~<>!]");
    +    var singleOperators = new RegExp("^[\\+\\-\\*/%&|\\^~<>!\\?]");
    +    // End IPython changes.
    +    
	 var singleDelimiters = new RegExp('^[\\(\\)\\[\\]\\{\\}@,:`=;\\.]');
	 var doubleOperators = new RegExp("^((==)|(!=)|(<=)|(>=)|(<>)|(<<)|(>>)|(//)|(\\*\\*))");
	 var doubleDelimiters = new RegExp("^((\\+=)|(\\-=)|(\\*=)|(%=)|(/=)|(&=)|(\\|=)|(\\^=))");


In practice it's just a one-line change, adding `\\?` to singleOperators,
surrounded by a comment.  We'll turn this into a proper patchset if it ever
gets more complicated than this, but for now this note should be enough.
