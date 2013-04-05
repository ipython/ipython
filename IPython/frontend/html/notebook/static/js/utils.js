//----------------------------------------------------------------------------
//  Copyright (C) 2008-2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Utilities
//============================================================================

IPython.namespace('IPython.utils');

IPython.utils = (function (IPython) {

    //============================================================================
    // Cross-browser RegEx Split
    //============================================================================

    // This code has been MODIFIED from the code licensed below to not replace the
    // default browser split.  The license is reproduced here.

    // see http://blog.stevenlevithan.com/archives/cross-browser-split for more info:
    /*!
     * Cross-Browser Split 1.1.1
     * Copyright 2007-2012 Steven Levithan <stevenlevithan.com>
     * Available under the MIT License
     * ECMAScript compliant, uniform cross-browser split method
     */

    /**
     * Splits a string into an array of strings using a regex or string
     * separator. Matches of the separator are not included in the result array.
     * However, if `separator` is a regex that contains capturing groups,
     * backreferences are spliced into the result each time `separator` is
     * matched. Fixes browser bugs compared to the native
     * `String.prototype.split` and can be used reliably cross-browser.
     * @param {String} str String to split.
     * @param {RegExp|String} separator Regex or string to use for separating
     *     the string.
     * @param {Number} [limit] Maximum number of items to include in the result
     *     array.
     * @returns {Array} Array of substrings.
     * @example
     *
     * // Basic use
     * regex_split('a b c d', ' ');
     * // -> ['a', 'b', 'c', 'd']
     *
     * // With limit
     * regex_split('a b c d', ' ', 2);
     * // -> ['a', 'b']
     *
     * // Backreferences in result array
     * regex_split('..word1 word2..', /([a-z]+)(\d+)/i);
     * // -> ['..', 'word', '1', ' ', 'word', '2', '..']
     */
    var regex_split = function (str, separator, limit) {
        // If `separator` is not a regex, use `split`
        if (Object.prototype.toString.call(separator) !== "[object RegExp]") {
            return split.call(str, separator, limit);
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

        compliantExecNpcg = typeof(/()??/.exec("")[1]) === "undefined"
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
        limit = typeof(limit) === "undefined" ?
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
                            if (typeof(arguments[i]) === "undefined") {
                                match[i] = undefined;
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

    //============================================================================
    // End contributed Cross-browser RegEx Split
    //============================================================================


    var uuid = function () {
        // http://www.ietf.org/rfc/rfc4122.txt
        var s = [];
        var hexDigits = "0123456789ABCDEF";
        for (var i = 0; i < 32; i++) {
            s[i] = hexDigits.substr(Math.floor(Math.random() * 0x10), 1);
        }
        s[12] = "4";  // bits 12-15 of the time_hi_and_version field to 0010
        s[16] = hexDigits.substr((s[16] & 0x3) | 0x8, 1);  // bits 6-7 of the clock_seq_hi_and_reserved to 01

        var uuid = s.join("");
        return uuid;
    };


    //Fix raw text to parse correctly in crazy XML
    function xmlencode(string) {
        return string.replace(/\&/g,'&'+'amp;')
            .replace(/</g,'&'+'lt;')
            .replace(/>/g,'&'+'gt;')
            .replace(/\'/g,'&'+'apos;')
            .replace(/\"/g,'&'+'quot;')
            .replace(/`/g,'&'+'#96;');
    }


    //Map from terminal commands to CSS classes
    ansi_colormap = {
        "30":"ansiblack", "31":"ansired",
        "32":"ansigreen", "33":"ansiyellow",
        "34":"ansiblue", "35":"ansipurple","36":"ansicyan",
        "37":"ansigrey", "01":"ansibold"
    };

    // Transform ANSI color escape codes into HTML <span> tags with css
    // classes listed in the above ansi_colormap object. The actual color used
    // are set in the css file.
    function fixConsole(txt) {
        txt = xmlencode(txt);
        var re = /\033\[([\dA-Fa-f;]*?)m/;
        var opened = false;
        var cmds = [];
        var opener = "";
        var closer = "";

        // Strip all ANSI codes that are not color related.  Matches
        // all ANSI codes that do not end with "m".
        var ignored_re = /(?=(\033\[[\d;=]*[a-ln-zA-Z]{1}))\1(?!m)/g;
        txt = txt.replace(ignored_re, "");

        while (re.test(txt)) {
            var cmds = txt.match(re)[1].split(";");
            closer = opened?"</span>":"";
            opened = cmds.length > 1 || cmds[0] != 0;
            var rep = [];
            for (var i in cmds)
                if (typeof(ansi_colormap[cmds[i]]) != "undefined")
                    rep.push(ansi_colormap[cmds[i]]);
            opener = rep.length > 0?"<span class=\""+rep.join(" ")+"\">":"";
            txt = txt.replace(re, closer + opener);
        }
        if (opened) txt += "</span>";
        return txt;
    }

    // Remove chunks that should be overridden by the effect of
    // carriage return characters
    function fixCarriageReturn(txt) {
        tmp = txt;
        do {
            txt = tmp;
            tmp = txt.replace(/\r+\n/gm, '\n'); // \r followed by \n --> newline
            tmp = tmp.replace(/^.*\r+/gm, '');  // Other \r --> clear line
        } while (tmp.length < txt.length);
        return txt;
    }

    // Locate URLs in plain text and wrap them in spaces so that they can be
    // better picked out by autoLinkUrls even after the text has been
    // converted to HTML
    function wrapUrls(txt) {
        // Note this regexp is a modified version of one from
        // Markdown.Converter For now it only supports http(s) and ftp URLs,
        // but could easily support others (though file:// should maybe be
        // avoided)
        var url_re = /(^|\W)(https?|ftp)(:\/\/[-A-Z0-9+&@#\/%?=~_|\[\]\(\)!:,\.;]*[-A-Z0-9+&@#\/%=~_|\[\]])($|\W)/gi;
        return txt.replace(url_re, "$1 $2$3 $4");
    }

    // Locate a URL with spaces around it and convert that to a anchor tag
    function autoLinkUrls(txt) {
        return txt.replace(/ ((https?|ftp):[^'">\s]+) /gi,
            "<a target=\"_blank\" href=\"$1\">$1</a>");
    }

    grow = function(element) {
        // Grow the cell by hand. This is used upon reloading from JSON, when the
        // autogrow handler is not called.
        var dom = element.get(0);
        var lines_count = 0;
        // modified split rule from
        // http://stackoverflow.com/questions/2035910/how-to-get-the-number-of-lines-in-a-textarea/2036424#2036424
        var lines = dom.value.split(/\r|\r\n|\n/);
        lines_count = lines.length;
        if (lines_count >= 1) {
            dom.rows = lines_count;
        } else {
            dom.rows = 1;
        }
    };

    // some keycodes that seem to be platform/browser independant
    var keycodes ={
                BACKSPACE:  8,
                TAB      :  9,
                ENTER    : 13,
                SHIFT    : 16,
                CTRL     : 17,
                CONTROL  : 17,
                ALT      : 18,
                ESC      : 27,
                SPACE    : 32,
                PGUP     : 33,
                PGDOWN   : 34,
                LEFT_ARROW: 37,
                LEFTARROW: 37,
                LEFT     : 37,
                UP_ARROW : 38,
                UPARROW  : 38,
                UP       : 38,
                RIGHT_ARROW:39,
                RIGHTARROW:39,
                RIGHT    : 39,
                DOWN_ARROW: 40,
                DOWNARROW: 40,
                DOWN     : 40,
    };


    points_to_pixels = function (points) {
        // A reasonably good way of converting between points and pixels.
        var test = $('<div style="display: none; width: 10000pt; padding:0; border:0;"></div>');
        $(body).append(test);
        var pixel_per_point = test.width()/10000;
        test.remove();
        return Math.floor(points*pixel_per_point);
    }


    return {
        regex_split : regex_split,
        uuid : uuid,
        fixConsole : fixConsole,
        keycodes : keycodes,
        grow : grow,
        fixCarriageReturn : fixCarriageReturn,
        wrapUrls : wrapUrls,
        autoLinkUrls : autoLinkUrls,
        points_to_pixels : points_to_pixels
    };

}(IPython));
