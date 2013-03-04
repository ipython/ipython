//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Utilities
//============================================================================

IPython.namespace('IPython.utils');

IPython.utils = (function (IPython) {

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
        uuid : uuid,
        fixConsole : fixConsole,
        keycodes : keycodes,
        grow : grow,
        fixCarriageReturn : fixCarriageReturn,
        points_to_pixels : points_to_pixels
    };

}(IPython));
