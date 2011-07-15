
//============================================================================
// Utilities
//============================================================================

IPython.namespace('IPython.utils')

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
            .replace(/`/g,'&'+'#96;')
    }

    //Map from terminal commands to CSS classes
    attrib = {
        "30":"cblack", "31":"cred",
        "32":"cgreen", "33":"cyellow",  
        "34":"cblue", "36":"ccyan", 
        "37":"cwhite", "01":"cbold"}

    //Fixes escaped console commands, IE colors. Turns them into HTML
    function fixConsole(txt) {
        txt = xmlencode(txt)
        var re = /\033\[([\d;]*?)m/
        var opened = false
        var cmds = []
        var opener = ""
        var closer = ""
        
        while (re.test(txt)) {
            var cmds = txt.match(re)[1].split(";")
            closer = opened?"</span>":""
            opened = cmds.length > 1 || cmds[0] != 0
            var rep = []
            for (var i in cmds)
                if (typeof(attrib[cmds[i]]) != "undefined")
                    rep.push(attrib[cmds[i]])
            opener = rep.length > 0?"<span class=\""+rep.join(" ")+"\">":""
            txt = txt.replace(re, closer + opener)
        }
        if (opened) txt += "</span>"
        return txt.trim()
    }

    return {
        uuid : uuid,
        fixConsole : fixConsole
    }

}(IPython));

