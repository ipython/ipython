// highly adapted for codemiror jshint

(function () {
  "use strict";
  function forEach(arr, f) {
    for (var i = 0, e = arr.length; i < e; ++i) f(arr[i]);
  }
  
  function arrayContains(arr, item) {
    if (!Array.prototype.indexOf) {
      var i = arr.length;
      while (i--) {
        if (arr[i] === item) {
          return true;
        }
      }
      return false;
    }
    return arr.indexOf(item) != -1;
  }
  
  CodeMirror.contextHint = function(editor) {
    // Find the token at the cursor
    var cur = editor.getCursor(), token = editor.getTokenAt(cur), tprop = token;
    // If it's not a 'word-style' token, ignore the token.
    // If it is a property, find out what it is a property of.

    var list  = new Array();
    var clist = getCompletions(token,editor) ;
    for( var i = 0 ; i < clist.length ; i++)    
    {
        list.push(
                {
                    str  : clist[i],
                    type : "context",
                    from : {line: cur.line, ch: token.start},
                    to   : {line: cur.line, ch: token.end}
                }
            )

    }
    return list;
  }

  // find all 'words' of current cell
  function getAllTokens(editor)
  {
    var found = [];
    // get all text remove and split it before dot and at space
    // keep the dot for completing token that also start with dot
    var candidates = editor.getValue()
        .replace(/[. ]/g,"\n") 
        .split('\n'); 
    // append to arry if not already (the function)
    function maybeAdd(str) {
      if (!arrayContains(found, str)) found.push(str);
    }

    // append to arry if not already 
    // (here we do it )
    for( var c in candidates )
    {
        if(candidates[c].length >= 1){
        maybeAdd(candidates[c]);}
    }
    return found;

  }

  function getCompletions(token,editor) 
  {
    var candidates = getAllTokens(editor);
    // filter all token that have a common start (but nox exactly) the lenght of the current token
    var prependchar ='';
    if(token.string.indexOf('.') == 0)
    {
        prependchar = '.'
    }
    var lambda = function(x){ 
        x = prependchar+x;
        return (x.indexOf(token.string)==0 && x != token.string)};
    var filterd = candidates.filter(lambda);
    for( var i in filterd)
    {
        // take care of reappending '.' at the beginning
        filterd[i] = prependchar+filterd[i];
    }
    return filterd;
  }
})();
