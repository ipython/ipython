$.ajaxSetup({
    url: client_id,
    dataType: "json"
})
$(document).ready(function() {
    comet = new CometGetter()
    heartbeat()
    manager = new Manager("messages")
    //Startup POST, set some globals
    $.ajax({
        type: "POST",
        data: {type:"connect"},
        success: function(json, status, request) {
            username = json.parent_header.username
            session = json.header.session
            exec_count = json.content.execution_count
            manager.get().activate()
        }
    })
    statusbar = new StatusBar("statusbar")
})

function fixConsole(txt) {
    //Fixes escaped console commands, IE colors. Turns them into HTML
    //Unfortunately, the "semantics" of html and console are very 
    //different, so fancy things *will* break
    var attrib = {"30":"cblack", "31":"cred","32":"cgreen", "34":"cblue", "36":"ccyan", "01":"cbold"}
    txt = txt.replace("<","&lt;").replace(">", "&gt;")
    var re = /\033\[([\d;]+?)m/
    var opened = false
    while (re.test(txt)) {
        var cmds = txt.match(re)[1].split(";")
        opened = cmds[0] != "0"
        var close = opened?"":"</span>"
        var rep = []
        for (var i in cmds)
            if (typeof(attrib[cmds[i]]) != "undefined")
                rep.push(attrib[cmds[i]])
        var open = rep.length > 0?"<span class=\""+rep.join(" ")+"\">":""
        txt = txt.replace(re, close + open)
    }
    if (opened) txt += "</span>"
    return txt
}

function inspect(obj) {
    if (obj instanceof Object) {
        var str = []
        for (var i in obj) 
            str.push(i+": "+inspect(obj[i]).replace("\n", "\n\t"))
        return "{\n\t"+str.join("\n\t")+"\n}\n"
    } else {
        try {
        return obj.toString()
        } catch (e) {
        }
        return ""
    }
}
