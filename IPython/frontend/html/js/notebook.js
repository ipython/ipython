/***********************************************************************
 #-----------------------------------------------------------------------------
 # Copyright (c) 2010, IPython Development Team.
 #
 # Distributed under the terms of the Modified BSD License.
 #
 # The full license is in the file COPYING.txt, distributed with this software.
 #-----------------------------------------------------------------------------
 
 Basic startup functions, environment
 ***********************************************************************/
//Setup defaults for any AJAX requests
$.ajaxSetup({
    url: client_id,
    dataType: "json"
})

//Things to initialize when the page is done loading
$(document).ready(function() {
    heartbeat()
    comet = new CometGetter()
    manager = new Manager("messages")
    statusbar = new StatusBar("statusbar")
    kernhistory = new History("history .inside")
    //Startup connection, set some globals
    //Currently a hack that looks like a messed up execute statement
    execute(" ")
})

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
//A smart modulus function, for possible negative values
function mod(x, y) {
    return ((x%y)+y)%y;
}

//Checks the appropriate indentation level
dedentKeys = /(raise|return|break|continue|yield|pass)/g
function checkIndent(code, pos) {
    code = code.slice(0,pos).split("\n")
    //Second to last one, the last one is the newline
    var last = code[code.length-2].trim()
    if (last[last.length-1] == ":")
        return 1
    else if (dedentKeys.test(last))
        return -1
    else
        return 0
}
