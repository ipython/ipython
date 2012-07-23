=======================
 CodeMirror in IPython
=======================

We carry a mostly unmodified copy of CodeMirror.  The current version we use
is (*please update this information when updating versions*)::

    CodeMirror2 4e244d252a26a2dba5446d44eb46adfb3c7f356a , tag : v2.32

The only changes we've applied so far are these::

    git show a66ebff60a2e36db13b

    commit a66ebff60a2e36db13bb5e17cf75e715eb18352e
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

and

    git show 05c4337f4768a1234681ea947cb684d343cf10a5 --stat
    commit 05c4337f4768a1234681ea947cb684d343cf10a5
    Author: Matthias BUSSONNIER <bussonniermatthias@gmail.com>
    Date:   Mon Jul 23 14:47:08 2012 +0200

        reintroduce ipython.css

     IPython/frontend/html/notebook/static/codemirror/theme/ipython.css | 40 ++++++++++++++++++++++++++++++++++++++++
     1 file changed, 40 insertions(+)

that you should eb able to apply after updating codemirror with

git cherry-pick 4e244d252 05c4337f

In practice it's just a one-line change, adding `\\?` to singleOperators,
surrounded by a comment.  We'll turn this into a proper patchset if it ever
gets more complicated than this, but for now this note should be enough.
