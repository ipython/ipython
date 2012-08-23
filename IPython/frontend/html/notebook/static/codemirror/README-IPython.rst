=======================
 CodeMirror in IPython
=======================

We carry a mostly unmodified copy of CodeMirror.  The current version we use
is (*please update this information when updating versions*)::

    CodeMirror2 4e244d252a26a2dba5446d44eb46adfb3c7f356a , tag : v2.32

The following CodeMirror commits have been cherry-picked into the source:

  * 4ec8a34 Pressing Up while on the first line should move cursor to (0,0)

The current politics is not to ships the following folders of CodeMirrors :

  * doc/
  * demo/
  * test/


The only changes we've applied so far are these::

    git show 271e17dd21f4f0c802a573b412e430998a70a78c

    commit 271e17dd21f4f0c802a573b412e430998a70a78c
    Author: Matthias BUSSONNIER <bussonniermatthias@gmail.com>
    Date:   Mon Jul 23 14:53:21 2012 +0200

        patch SingleOperator in CodeMirror2

    diff --git a/IPython/frontend/html/notebook/static/codemirror/mode/python/python.js b/IPython/frontend/html/notebook/static/code
    index d6888e8..201da51 100644
    --- a/IPython/frontend/html/notebook/static/codemirror/mode/python/python.js
    +++ b/IPython/frontend/html/notebook/static/codemirror/mode/python/python.js
    @@ -4,8 +4,11 @@ CodeMirror.defineMode("python", function(conf, parserConf) {
         function wordRegexp(words) {
             return new RegExp("^((" + words.join(")|(") + "))\\b");
         }
    -
    -    var singleOperators = new RegExp("^[\\+\\-\\*/%&|\\^~<>!]");
    +
    +    // IPython-specific changes: add '?' as recognized character.
    +    var singleOperators = new RegExp("^[\\+\\-\\*/%&|\\^~<>!\\?]");
    +    // End IPython changes.
    +
         var singleDelimiters = new RegExp('^[\\(\\)\\[\\]\\{\\}@,:`=;\\.]');
         var doubleOperators = new RegExp("^((==)|(!=)|(<=)|(>=)|(<>)|(<<)|(>>)|(//)|(\\*\\*))");
         var doubleDelimiters = new RegExp("^((\\+=)|(\\-=)|(\\*=)|(%=)|(/=)|(&=)|(\\|=)|(\\^=))");

In practice it's just a one-line change, adding `\\?` to singleOperators,
surrounded by a comment. 

Then don't forget to reintroduce ipython.css

    git show 39a602468ee1ca8fdb660826d6185e0f9a026fdf --stat
    commit 39a602468ee1ca8fdb660826d6185e0f9a026fdf
    Author: Matthias BUSSONNIER <bussonniermatthias@gmail.com>
    Date:   Mon Jul 23 14:47:08 2012 +0200

        reintroduce ipython.css

     IPython/frontend/html/notebook/static/codemirror/theme/ipython.css | 40 ++++++++++++++++++++++++++++++++++++++++
     1 file changed, 40 insertions(+)

and 

    git show head^
    commit 331a5f7fe85a6e894c35b64cd7987ed53f59ea57
    Author: Matthias BUSSONNIER <bussonniermatthias@gmail.com>
    Date:   Wed Jul 25 12:41:13 2012 +0200

        patch deletion in codemirror

    diff --git a/IPython/frontend/html/notebook/static/codemirror/lib/codemirror.js b/IPython/frontend/html/notebook/static/codemirror/lib/codemirror.js
    index 89401a9..a9dfdfe 100644
    --- a/IPython/frontend/html/notebook/static/codemirror/lib/codemirror.js
    +++ b/IPython/frontend/html/notebook/static/codemirror/lib/codemirror.js
    @@ -2194,6 +2194,20 @@ var CodeMirror = (function() {
        cm.indentLine(cm.getCursor().line);
        },
        toggleOverwrite: function(cm) {cm.toggleOverwrite();}
    +    ,delSpaceToPrevTabStop : function(cm){
    +        var from = cm.getCursor(true), to = cm.getCursor(false), sel = !posEq(from, to);
    +        if (!posEq(from, to)) {cm.replaceRange("", from, to); return}
    +        var cur = cm.getCursor(), line = cm.getLine(cur.line);
    +        var tabsize = cm.getOption('tabSize');
    +        var chToPrevTabStop = cur.ch-(Math.ceil(cur.ch/tabsize)-1)*tabsize;
    +        var from = {ch:cur.ch-chToPrevTabStop,line:cur.line}
    +        var select = cm.getRange(from,cur)
    +        if( select.match(/^\ +$/) != null){
    +            cm.replaceRange("",from,cur)
    +        } else {
    +            cm.deleteH(-1,"char")
    +        }
    +    }
    };
    
    var keyMap = CodeMirror.keyMap = {};

that you should be able to apply after updating codemirror with

git cherry-pick 271e17 39a602 331a5f

We'll turn this into a proper patchset if it ever gets more complicated than
this, but for now this note should be enough.
