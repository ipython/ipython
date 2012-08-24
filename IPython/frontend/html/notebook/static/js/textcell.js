//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Cross-browser RegEx Split
//============================================================================

// see http://blog.stevenlevithan.com/archives/cross-browser-split for more info:
/*!
 * Cross-Browser Split 1.1.1
 * Copyright 2007-2012 Steven Levithan <stevenlevithan.com>
 * Available under the MIT License
 * ECMAScript compliant, uniform cross-browser split method
 */

/**
 * Splits a string into an array of strings using a regex or string separator. Matches of the
 * separator are not included in the result array. However, if `separator` is a regex that contains
 * capturing groups, backreferences are spliced into the result each time `separator` is matched.
 * Fixes browser bugs compared to the native `String.prototype.split` and can be used reliably
 * cross-browser.
 * @param {String} str String to split.
 * @param {RegExp|String} separator Regex or string to use for separating the string.
 * @param {Number} [limit] Maximum number of items to include in the result array.
 * @returns {Array} Array of substrings.
 * @example
 *
 * // Basic use
 * split('a b c d', ' ');
 * // -> ['a', 'b', 'c', 'd']
 *
 * // With limit
 * split('a b c d', ' ', 2);
 * // -> ['a', 'b']
 *
 * // Backreferences in result array
 * split('..word1 word2..', /([a-z]+)(\d+)/i);
 * // -> ['..', 'word', '1', ' ', 'word', '2', '..']
 */
var split;

// Avoid running twice; that would break the `nativeSplit` reference
split = split || function (undef) {

    var nativeSplit = String.prototype.split,
        compliantExecNpcg = /()??/.exec("")[1] === undef, // NPCG: nonparticipating capturing group
        self;

    self = function (str, separator, limit) {
        // If `separator` is not a regex, use `nativeSplit`
        if (Object.prototype.toString.call(separator) !== "[object RegExp]") {
            return nativeSplit.call(str, separator, limit);
        }
        var output = [],
            flags = (separator.ignoreCase ? "i" : "") +
                    (separator.multiline  ? "m" : "") +
                    (separator.extended   ? "x" : "") + // Proposed for ES6
                    (separator.sticky     ? "y" : ""), // Firefox 3+
            lastLastIndex = 0,
            // Make `global` and avoid `lastIndex` issues by working with a copy
            separator = new RegExp(separator.source, flags + "g"),
            separator2, match, lastIndex, lastLength;
        str += ""; // Type-convert
        if (!compliantExecNpcg) {
            // Doesn't need flags gy, but they don't hurt
            separator2 = new RegExp("^" + separator.source + "$(?!\\s)", flags);
        }
        /* Values for `limit`, per the spec:
         * If undefined: 4294967295 // Math.pow(2, 32) - 1
         * If 0, Infinity, or NaN: 0
         * If positive number: limit = Math.floor(limit); if (limit > 4294967295) limit -= 4294967296;
         * If negative number: 4294967296 - Math.floor(Math.abs(limit))
         * If other: Type-convert, then use the above rules
         */
        limit = limit === undef ?
            -1 >>> 0 : // Math.pow(2, 32) - 1
            limit >>> 0; // ToUint32(limit)
        while (match = separator.exec(str)) {
            // `separator.lastIndex` is not reliable cross-browser
            lastIndex = match.index + match[0].length;
            if (lastIndex > lastLastIndex) {
                output.push(str.slice(lastLastIndex, match.index));
                // Fix browsers whose `exec` methods don't consistently return `undefined` for
                // nonparticipating capturing groups
                if (!compliantExecNpcg && match.length > 1) {
                    match[0].replace(separator2, function () {
                        for (var i = 1; i < arguments.length - 2; i++) {
                            if (arguments[i] === undef) {
                                match[i] = undef;
                            }
                        }
                    });
                }
                if (match.length > 1 && match.index < str.length) {
                    Array.prototype.push.apply(output, match.slice(1));
                }
                lastLength = match[0].length;
                lastLastIndex = lastIndex;
                if (output.length >= limit) {
                    break;
                }
            }
            if (separator.lastIndex === match.index) {
                separator.lastIndex++; // Avoid an infinite loop
            }
        }
        if (lastLastIndex === str.length) {
            if (lastLength || !separator.test("")) {
                output.push("");
            }
        } else {
            output.push(str.slice(lastLastIndex));
        }
        return output.length > limit ? output.slice(0, limit) : output;
    };

    // For convenience
    String.prototype.split = function (separator, limit) {
        return self(this, separator, limit);
    };

    return self;

}();

//============================================================================
// TextCell
//============================================================================

var IPython = (function (IPython) {

    // TextCell base class
    var key = IPython.utils.keycodes;

    var TextCell = function () {
        this.code_mirror_mode = this.code_mirror_mode || 'htmlmixed';
        IPython.Cell.apply(this, arguments);
        this.rendered = false;
        this.cell_type = this.cell_type || 'text';
    };


    TextCell.prototype = new IPython.Cell();


    TextCell.prototype.create_element = function () {
        var cell = $("<div>").addClass('cell text_cell border-box-sizing');
        cell.attr('tabindex','2');
        var input_area = $('<div/>').addClass('text_cell_input border-box-sizing');
        this.code_mirror = CodeMirror(input_area.get(0), {
            indentUnit : 4,
            mode: this.code_mirror_mode,
            theme: 'default',
            value: this.placeholder,
            readOnly: this.read_only,
            lineWrapping : true,
            extraKeys: {"Tab": "indentMore","Shift-Tab" : "indentLess"},
            onKeyEvent: $.proxy(this.handle_codemirror_keyevent,this)
        });
        // The tabindex=-1 makes this div focusable.
        var render_area = $('<div/>').addClass('text_cell_render border-box-sizing').
            addClass('rendered_html').attr('tabindex','-1');
        cell.append(input_area).append(render_area);
        this.element = cell;
    };


    TextCell.prototype.bind_events = function () {
        IPython.Cell.prototype.bind_events.apply(this);
        var that = this;
        this.element.keydown(function (event) {
            if (event.which === 13 && !event.shiftKey) {
                if (that.rendered) {
                    that.edit();
                    return false;
                };
            };
        });
        this.element.dblclick(function () {
            that.edit();
        });
    };


    TextCell.prototype.handle_codemirror_keyevent = function (editor, event) {
        // This method gets called in CodeMirror's onKeyDown/onKeyPress
        // handlers and is used to provide custom key handling. Its return
        // value is used to determine if CodeMirror should ignore the event:
        // true = ignore, false = don't ignore.
        
        if (event.keyCode === 13 && (event.shiftKey || event.ctrlKey)) {
            // Always ignore shift-enter in CodeMirror as we handle it.
            return true;
        }
        return false;
    };


    TextCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        var output = this.element.find("div.text_cell_render");
        output.trigger('focus');
    };


    TextCell.prototype.unselect = function() {
        // render on selection of another cell
        this.render();
        IPython.Cell.prototype.unselect.apply(this);
    };


    TextCell.prototype.edit = function () {
        if ( this.read_only ) return;
        if (this.rendered === true) {
            var text_cell = this.element;
            var output = text_cell.find("div.text_cell_render");  
            output.hide();
            text_cell.find('div.text_cell_input').show();
            this.code_mirror.refresh();
            this.code_mirror.focus();
            // We used to need an additional refresh() after the focus, but
            // it appears that this has been fixed in CM. This bug would show
            // up on FF when a newly loaded markdown cell was edited.
            this.rendered = false;
            if (this.get_text() === this.placeholder) {
                this.set_text('');
                this.refresh();
            }
        }
    };


    // Subclasses must define render.
    TextCell.prototype.render = function () {};


    TextCell.prototype.get_text = function() {
        return this.code_mirror.getValue();
    };


    TextCell.prototype.set_text = function(text) {
        this.code_mirror.setValue(text);
        this.code_mirror.refresh();
    };


    TextCell.prototype.get_rendered = function() {
        return this.element.find('div.text_cell_render').html();
    };


    TextCell.prototype.set_rendered = function(text) {
        this.element.find('div.text_cell_render').html(text);
    };


    TextCell.prototype.at_top = function () {
        if (this.rendered) {
            return true;
        } else {
            return false;
        }
    };


    TextCell.prototype.at_bottom = function () {
        if (this.rendered) {
            return true;
        } else {
            return false;
        }
    };


    TextCell.prototype.fromJSON = function (data) {
        IPython.Cell.prototype.fromJSON.apply(this, arguments);
        if (data.cell_type === this.cell_type) {
            if (data.source !== undefined) {
                this.set_text(data.source);
                // make this value the starting point, so that we can only undo
                // to this state, instead of a blank cell
                this.code_mirror.clearHistory();
                this.set_rendered(data.rendered || '');
                this.rendered = false;
                this.render();
            }
        }
    };


    TextCell.prototype.toJSON = function () {
        var data = IPython.Cell.prototype.toJSON.apply(this);
        data.cell_type = this.cell_type;
        data.source = this.get_text();
        return data;
    };


    // HTMLCell

    var HTMLCell = function () {
        this.placeholder = "Type <strong>HTML</strong> and LaTeX: $\\alpha^2$";
        IPython.TextCell.apply(this, arguments);
        this.cell_type = 'html';
    };


    HTMLCell.prototype = new TextCell();


    HTMLCell.prototype.render = function () {
        if (this.rendered === false) {
            var text = this.get_text();
            if (text === "") { text = this.placeholder; }
            this.set_rendered(text);
            this.typeset();
            this.element.find('div.text_cell_input').hide();
            this.element.find("div.text_cell_render").show();
            this.rendered = true;
        }
    };


    // MarkdownCell

    // Some magic for deferring mathematical expressions to MathJaX
    // Some of the logic here is reused with permission from Stack Exchange Inc.

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
        
        blocks = text.replace(/\r\n?/g, "\n").split(MATHSPLIT);
        
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

    var MarkdownCell = function () {
        this.placeholder = "Type *Markdown* and LaTeX: $\\alpha^2$";
        IPython.TextCell.apply(this, arguments);
        this.cell_type = 'markdown';
    };


    MarkdownCell.prototype = new TextCell();


    MarkdownCell.prototype.render = function () {
        if (this.rendered === false) {
            var text = this.get_text();
            if (text === "") { text = this.placeholder; }

            text = removeMath(text)
            var html = IPython.markdown_converter.makeHtml(text);
            html = replaceMath(html)

            this.set_rendered(html);
            try {
                this.set_rendered(html);
            } catch (e) {
                console.log("Error running Javascript in Markdown:");
                console.log(e);
                this.set_rendered($("<div/>").addClass("js-error").html(
                    "Error rendering Markdown!<br/>" + e.toString())
                );
            }
            this.typeset()
            this.element.find('div.text_cell_input').hide();
            this.element.find("div.text_cell_render").show();
            var code_snippets = this.element.find("pre > code");
            code_snippets.replaceWith(function () {
                var code = $(this).html();
                /* Substitute br for newlines and &nbsp; for spaces
                   before highlighting, since prettify doesn't
                   preserve those on all browsers */
                code = code.replace(/(\r\n|\n|\r)/gm, "<br/>");
                code = code.replace(/ /gm, '&nbsp;');
                code = prettyPrintOne(code);

                return '<code class="prettyprint">' + code + '</code>';
            });
            this.rendered = true;
        }
    };


    // RawCell

    var RawCell = function () {
        this.placeholder = "Type plain text and LaTeX: $\\alpha^2$";
        this.code_mirror_mode = 'rst';
        IPython.TextCell.apply(this, arguments);
        this.cell_type = 'raw';
    };


    RawCell.prototype = new TextCell();


    RawCell.prototype.render = function () {
        this.rendered = true;
        this.edit();
    };


    RawCell.prototype.handle_codemirror_keyevent = function (editor, event) {
        // This method gets called in CodeMirror's onKeyDown/onKeyPress
        // handlers and is used to provide custom key handling. Its return
        // value is used to determine if CodeMirror should ignore the event:
        // true = ignore, false = don't ignore.

        var that = this;
        if (event.which === key.UPARROW && event.type === 'keydown') {
            // If we are not at the top, let CM handle the up arrow and
            // prevent the global keydown handler from handling it.
            if (!that.at_top()) {
                event.stop();
                return false;
            } else {
                return true;
            };
        } else if (event.which === key.DOWNARROW && event.type === 'keydown') {
            // If we are not at the bottom, let CM handle the down arrow and
            // prevent the global keydown handler from handling it.
            if (!that.at_bottom()) {
                event.stop();
                return false;
            } else {
                return true;
            };
        };
        return false;
    };


    RawCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        this.code_mirror.refresh();
        this.code_mirror.focus();
    };


    RawCell.prototype.at_top = function () {
        var cursor = this.code_mirror.getCursor();
        if (cursor.line === 0 && cursor.ch === 0) {
            return true;
        } else {
            return false;
        }
    };


    RawCell.prototype.at_bottom = function () {
        var cursor = this.code_mirror.getCursor();
        if (cursor.line === (this.code_mirror.lineCount()-1) && cursor.ch === this.code_mirror.getLine(cursor.line).length) {
            return true;
        } else {
            return false;
        }
    };


    // HTMLCell

    var HeadingCell = function () {
        this.placeholder = "Type Heading Here";
        IPython.TextCell.apply(this, arguments);
        this.cell_type = 'heading';
        this.level = 1;
    };


    HeadingCell.prototype = new TextCell();


    HeadingCell.prototype.fromJSON = function (data) {
        if (data.level != undefined){
            this.level = data.level;
        }
        IPython.TextCell.prototype.fromJSON.apply(this, arguments);
    };


    HeadingCell.prototype.toJSON = function () {
        var data = IPython.TextCell.prototype.toJSON.apply(this);
        data.level = this.get_level();
        return data;
    };


    HeadingCell.prototype.set_level = function (level) {
        this.level = level;
        if (this.rendered) {
            this.rendered = false;
            this.render();
        };
    };


    HeadingCell.prototype.get_level = function () {
        return this.level;
    };


    HeadingCell.prototype.set_rendered = function (text) {
        var r = this.element.find("div.text_cell_render");
        r.empty();
        r.append($('<h'+this.level+'/>').html(text));
    };


    HeadingCell.prototype.get_rendered = function () {
        var r = this.element.find("div.text_cell_render");
        return r.children().first().html();
    };


    HeadingCell.prototype.render = function () {
        if (this.rendered === false) {
            var text = this.get_text();
            if (text === "") { text = this.placeholder; }
            this.set_rendered(text);
            this.typeset();
            this.element.find('div.text_cell_input').hide();
            this.element.find("div.text_cell_render").show();
            this.rendered = true;
        };
    };

    IPython.TextCell = TextCell;
    IPython.HTMLCell = HTMLCell;
    IPython.MarkdownCell = MarkdownCell;
    IPython.RawCell = RawCell;
    IPython.HeadingCell = HeadingCell;


    return IPython;

}(IPython));

