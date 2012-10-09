//----------------------------------------------------------------------------
//  Copyright (C) 2008-2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// MathJax utility functions
//============================================================================

IPython.namespace('IPython.mathjaxutils');

IPython.mathjaxutils = (function (IPython) {

    var init = function () {
        if (window.MathJax) { 
            // MathJax loaded
            MathJax.Hub.Config({
                TeX: { equationNumbers: { autoNumber: "AMS", useLabelIds: true } },
                tex2jax: {
                    inlineMath: [ ['$','$'], ["\\(","\\)"] ],
                    displayMath: [ ['$$','$$'], ["\\[","\\]"] ],
                    processEnvironments: true
                },
                displayAlign: 'left', // Change this to 'center' to center equations.
                "HTML-CSS": {
                    styles: {'.MathJax_Display': {"margin": 0}}
                }
            });
        } else if (window.mathjax_url != "") {
            // Don't have MathJax, but should. Show dialog.
            var dialog = $('<div></div>')
                .append(
                    $("<p></p>").addClass('dialog').html(
                        "Math/LaTeX rendering will be disabled."
                    )
                ).append(
                    $("<p></p>").addClass('dialog').html(
                        "If you have administrative access to the notebook server and" +
                        " a working internet connection, you can install a local copy" +
                        " of MathJax for offline use with the following command on the server" +
                        " at a Python or IPython prompt:"
                    )
                ).append(
                    $("<pre></pre>").addClass('dialog').html(
                        ">>> from IPython.external import mathjax; mathjax.install_mathjax()"
                    )
                ).append(
                    $("<p></p>").addClass('dialog').html(
                        "This will try to install MathJax into the IPython source directory."
                    )
                ).append(
                    $("<p></p>").addClass('dialog').html(
                        "If IPython is installed to a location that requires" +
                        " administrative privileges to write, you will need to make this call as" +
                        " an administrator, via 'sudo'."
                    )
                ).append(
                    $("<p></p>").addClass('dialog').html(
                        "When you start the notebook server, you can instruct it to disable MathJax support altogether:"
                    )
                ).append(
                    $("<pre></pre>").addClass('dialog').html(
                        "$ ipython notebook --no-mathjax"
                    )
                ).append(
                    $("<p></p>").addClass('dialog').html(
                        "which will prevent this dialog from appearing."
                    )
                ).dialog({
                    title: "Failed to retrieve MathJax from '" + window.mathjax_url + "'",
                    width: "70%",
                    modal: true,
                })
        } else {
            // No MathJax, but none expected. No dialog.
        };
    };

    // Some magic for deferring mathematical expressions to MathJaX
    // Some of the code here is adapted with permission from Stack Exchange Inc.

    var inline = "$"; // the inline math delimiter
    var blocks, start, end, last, braces; // used in searching for math
    var math; // stores math until pagedown (Markdown parser) is done
    var HUB = MathJax.Hub;

    // MATHSPLIT contains the pattern for math delimiters and special symbols
    // needed for searching for math in the text input.   
    var MATHSPLIT = /(\$\$?|\\(?:begin|end)\{[a-z]*\*?\}|\\[\\{}$]|[{}]|(?:\n\s*)+|@@\d+@@)/i;

    //  The math is in blocks i through j, so 
    //    collect it into one block and clear the others.
    //  Replace &, <, and > by named entities.
    //  For IE, put <br> at the ends of comments since IE removes \n.
    //  Clear the current math positions and store the index of the
    //    math, then push the math string onto the storage array.
    //  The preProcess function is called on all blocks if it has been passed in
    function processMath(i, j, preProcess) {
        var block = blocks.slice(i, j + 1).join("").replace(/&/g, "&amp;") // use HTML entity for &
        .replace(/</g, "&lt;") // use HTML entity for <
        .replace(/>/g, "&gt;") // use HTML entity for >
        ;
        if (HUB.Browser.isMSIE) {
            block = block.replace(/(%[^\n]*)\n/g, "$1<br/>\n")
        }
        while (j > i) {
            blocks[j] = "";
            j--;
        }
        blocks[i] = "@@" + math.length + "@@"; // replace the current block text with a unique tag to find later
        if (preProcess)
            block = preProcess(block);
        math.push(block);
        start = end = last = null;
    }

    //  Break up the text into its component parts and search
    //    through them for math delimiters, braces, linebreaks, etc.
    //  Math delimiters must match and braces must balance.
    //  Don't allow math to pass through a double linebreak
    //    (which will be a paragraph).
    //
    function removeMath(text) {
        start = end = last = null; // for tracking math delimiters
        math = []; // stores math strings for later
        
        // Except for extreme edge cases, this should catch precisely those pieces of the markdown
        // source that will later be turned into code spans. While MathJax will not TeXify code spans,
        // we still have to consider them at this point; the following issue has happened several times:
        //
        //     `$foo` and `$bar` are varibales.  -->  <code>$foo ` and `$bar</code> are variables.

        var hasCodeSpans = /`/.test(text),
            deTilde;
        if (hasCodeSpans) {
            text = text.replace(/~/g, "~T").replace(/(^|[^\\])(`+)([^\n]*?[^`\n])\2(?!`)/gm, function (wholematch) {
                return wholematch.replace(/\$/g, "~D");
            });
            deTilde = function (text) { return text.replace(/~([TD])/g, function (wholematch, character) { return { T: "~", D: "$" }[character]; }) };
        } else {
            deTilde = function (text) { return text; };
        }
        
        blocks = IPython.utils.regex_split(text.replace(/\r\n?/g, "\n"),MATHSPLIT);

        for (var i = 1, m = blocks.length; i < m; i += 2) {
            var block = blocks[i];
            if (block.charAt(0) === "@") {
                //
                //  Things that look like our math markers will get
                //  stored and then retrieved along with the math.
                //
                blocks[i] = "@@" + math.length + "@@";
                math.push(block);
            }
            else if (start) {
                //
                //  If we are in math, look for the end delimiter,
                //    but don't go past double line breaks, and
                //    and balance braces within the math.
                //
                if (block === end) {
                    if (braces) {
                        last = i
                    }
                    else {
                        processMath(start, i, deTilde)
                    }
                }
                else if (block.match(/\n.*\n/)) {
                    if (last) {
                        i = last;
                        processMath(start, i, deTilde)
                    }
                    start = end = last = null;
                    braces = 0;
                }
                else if (block === "{") {
                    braces++
                }
                else if (block === "}" && braces) {
                    braces--
                }
            }
            else {
                //
                //  Look for math start delimiters and when
                //    found, set up the end delimiter.
                //
                if (block === inline || block === "$$") {
                    start = i;
                    end = block;
                    braces = 0;
                }
                else if (block.substr(1, 5) === "begin") {
                    start = i;
                    end = "\\end" + block.substr(6);
                    braces = 0;
                }
            }
        }
        if (last) {
            processMath(start, last, deTilde)
        }
        return deTilde(blocks.join(""));
    }

    //
    //  Put back the math strings that were saved,
    //    and clear the math array (no need to keep it around).
    //  
    function replaceMath(text) {
        text = text.replace(/@@(\d+)@@/g, function (match, n) {
            return math[n]
        });
        math = null;
        return text;
    }

    function queueRender() {
        // see https://groups.google.com/forum/?fromgroups=#!topic/mathjax-users/cpwy5eCH1ZQ
        MathJax.Hub.Queue( 
          ["resetEquationNumbers",MathJax.InputJax.TeX], 
          ["PreProcess",MathJax.Hub], 
          ["Reprocess",MathJax.Hub] 
          ); 
    }

    return {
        init : init,
        processMath : processMath,
        removeMath : removeMath,
        replaceMath : replaceMath,
        queueRender : queueRender
    };

}(IPython));