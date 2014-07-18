// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'base/js/dialog',
], function(IPython, $, utils, dialog) {
    "use strict";

    var init = function () {
        if (window.MathJax) {
            // MathJax loaded
            MathJax.Hub.Config({
                tex2jax: {
                    inlineMath: [ ['$','$'], ["\\(","\\)"] ],
                    displayMath: [ ['$$','$$'], ["\\[","\\]"] ],
                    processEscapes: true,
                    processEnvironments: true
                },
                // Center justify equations in code and markdown cells. Elsewhere
                // we use CSS to left justify single line equations in code cells.
                displayAlign: 'center',
                "HTML-CSS": {
                    styles: {'.MathJax_Display': {"margin": 0}},
                    linebreaks: { automatic: true }
                }
            });
            MathJax.Hub.Configured();
        } else if (window.mathjax_url !== "") {
            // Don't have MathJax, but should. Show dialog.
            var message = $('<div/>')
                .append(
                    $("<p/></p>").addClass('dialog').text(
                        "Math/LaTeX rendering will be disabled."
                    )
                ).append(
                    $("<p></p>").addClass('dialog').text(
                        "If you have administrative access to the notebook server and" +
                        " a working internet connection, you can install a local copy" +
                        " of MathJax for offline use with the following command on the server" +
                        " at a Python or IPython prompt:"
                    )
                ).append(
                    $("<pre></pre>").addClass('dialog').text(
                        ">>> from IPython.external import mathjax; mathjax.install_mathjax()"
                    )
                ).append(
                    $("<p></p>").addClass('dialog').text(
                        "This will try to install MathJax into the IPython source directory."
                    )
                ).append(
                    $("<p></p>").addClass('dialog').text(
                        "If IPython is installed to a location that requires" +
                        " administrative privileges to write, you will need to make this call as" +
                        " an administrator, via 'sudo'."
                    )
                ).append(
                    $("<p></p>").addClass('dialog').text(
                        "When you start the notebook server, you can instruct it to disable MathJax support altogether:"
                    )
                ).append(
                    $("<pre></pre>").addClass('dialog').text(
                        "$ ipython notebook --no-mathjax"
                    )
                ).append(
                    $("<p></p>").addClass('dialog').text(
                        "which will prevent this dialog from appearing."
                    )
                );
            dialog.modal({
                title : "Failed to retrieve MathJax from '" + window.mathjax_url + "'",
                body : message,
                buttons : {
                    OK : {class: "btn-danger"}
                }
            });
        }
    };

    // Some magic for deferring mathematical expressions to MathJax
    // by hiding them from the Markdown parser.
    // Some of the code here is adapted with permission from Davide Cervone
    // under the terms of the Apache2 license governing the MathJax project.
    // Other minor modifications are also due to StackExchange and are used with
    // permission.

    var inline = "$"; // the inline math delimiter

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
    var process_math = function (i, j, pre_process, math, blocks) {
        var block = blocks.slice(i, j + 1).join("").replace(/&/g, "&amp;") // use HTML entity for &
        .replace(/</g, "&lt;") // use HTML entity for <
        .replace(/>/g, "&gt;") // use HTML entity for >
        ;
        if (utils.browser === 'msie') {
            block = block.replace(/(%[^\n]*)\n/g, "$1<br/>\n");
        }
        while (j > i) {
            blocks[j] = "";
            j--;
        }
        blocks[i] = "@@" + math.length + "@@"; // replace the current block text with a unique tag to find later
        if (pre_process){
            block = pre_process(block);
        }
        math.push(block);
        return blocks;
    };

    //  Break up the text into its component parts and search
    //    through them for math delimiters, braces, linebreaks, etc.
    //  Math delimiters must match and braces must balance.
    //  Don't allow math to pass through a double linebreak
    //    (which will be a paragraph).
    //
    var remove_math = function (text) {
        var math = []; // stores math strings for later
        var start;
        var end;
        var last;
        var braces;

        // Except for extreme edge cases, this should catch precisely those pieces of the markdown
        // source that will later be turned into code spans. While MathJax will not TeXify code spans,
        // we still have to consider them at this point; the following issue has happened several times:
        //
        //     `$foo` and `$bar` are varibales.  -->  <code>$foo ` and `$bar</code> are variables.

        var hasCodeSpans = /`/.test(text),
            de_tilde;
        if (hasCodeSpans) {
            text = text.replace(/~/g, "~T").replace(/(^|[^\\])(`+)([^\n]*?[^`\n])\2(?!`)/gm, function (wholematch) {
                return wholematch.replace(/\$/g, "~D");
            });
            de_tilde = function (text) {
                return text.replace(/~([TD])/g, function (wholematch, character) {
                                                    return { T: "~", D: "$" }[character];
                                                });
            };
        } else {
            de_tilde = function (text) { return text; };
        }

        var blocks = utils.regex_split(text.replace(/\r\n?/g, "\n"),MATHSPLIT);

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
                        last = i;
                    }
                    else {
                        blocks = process_math(start, i, de_tilde, math, blocks);
                        start  = null;
                        end    = null;
                        last   = null;
                    }
                }
                else if (block.match(/\n.*\n/)) {
                    if (last) {
                        i = last;
                        blocks = process_math(start, i, de_tilde, math, blocks);
                    }
                    start = null;
                    end = null;
                    last = null;
                    braces = 0;
                }
                else if (block === "{") {
                    braces++;
                }
                else if (block === "}" && braces) {
                    braces--;
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
            blocks = process_math(start, last, de_tilde, math, blocks);
            start  = null;
            end    = null;
            last   = null;
        }
        return [de_tilde(blocks.join("")), math];
    };

    //
    //  Put back the math strings that were saved,
    //    and clear the math array (no need to keep it around).
    //
    var replace_math = function (text, math) {
        text = text.replace(/@@(\d+)@@/g, function (match, n) {
            return math[n];
        });
        return text;
    };

    var mathjaxutils = {
        init : init,
        remove_math : remove_math,
        replace_math : replace_math
    };

    IPython.mathjaxutils = mathjaxutils;

    return mathjaxutils;
});
