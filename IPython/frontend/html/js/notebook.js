function fixConsole(txt) {
    //Fixes escaped console commands, IE colors. Turns them into HTML
    //Unfortunately, the "semantics" of html and console are very 
    //different, so fancy things *will* break
    var attrib = {"30":"cblack", "31":"cred","32":"cgreen", "34":"cblue", "36":"ccyan", "01":"cbold"}
    txt = txt.replace("<","&lt;").replace(">", "&gt;")
    var re = /\033\[([\d;]+?)m/
    var opened = false
    while (re.test(txt)) {
        var cmds = re.exec(txt)[1].split(";")
        var close = opened?"</span>":""
        opened = cmds[0] == "0"?false:true
        var rep = []
        for (var i in cmds)
            rep.push(attrib[cmds[i]])
        var open = rep.length > 0?"<span class=\""+rep.join(" ")+"\">":""
        txt = txt.replace(re, close + open)
    }
    if (opened) txt += "</span>"
    return txt
}
function comet() {
    $.ajax({
        success: function(json, status, request) {
            comet()
            if (json.msg_type == "status") {
                statusbar.set(json.content.execution_state)
            } else {
                var msg = manager.get(json.parent_header.msg_id)
                if (json.msg_type == "stream") {
                    msg.setOutput(fixConsole(json.content.data))
                } else if (json.msg_type == "pyin") {
                    msg.setInput(fixConsole(json.content.code))
                } else if (json.msg_type == "pyout") {
                    msg.setOutput(fixConsole(json.content.data), true)
                } else if (json.msg_type == "pyerr") {
                    msg.setOutput(fixConsole(json.content.traceback.join("\n")))
                }
            }
        }
    })
}
function heartbeat() {
    $.ajax({
        type: "POST",
        data: {client_id:client_id, type:"heartbeat"},
        success: function() {
            setTimeout(heartbeat, 10000)
        }
    })
}
function execute(code) {
    $.ajax({
        type: "POST",
        data: {type:"execute", code:code},
        success: function(json, status, request) {
            if (json != null) {
                exec_count = json.content.execution_count
                if (json.content.payload.length > 0 && 
                    json.content.payload[0]['format'] == "svg") {
                    var svg = document.createElement('object')
                    svg.setAttribute('class', "inlinesvg")
                    svg.setAttribute('type', 'image/svg+xml')
                    svg.setAttribute('data', 'data:image/svg+xml,'+ 
                        json.content.payload[0]['data'])
                    manager.get(json.parent_header.msg_id).setOutput("<br />")                
                    manager.get(json.parent_header.msg_id).setOutput(svg)
                }
            }

        }
    })
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

function StatusBar(obj) {
    $("#"+obj).append("<span class='txt'></span>")
    $("#"+obj).append("<span class='bullet'>&#8226;</span>")
    this.text = $("#"+obj+" .txt")
    this.bullet = $("#"+obj+" .bullet")
}
StatusBar.prototype.map = { "idle":"cgreen", "busy":"cyellow", "dead":"cred" }
StatusBar.prototype.set = function(status) {
    this.bullet.removeClass()
    this.bullet.addClass("bullet "+this.map[status])
    this.text.text(status)
}


function Manager(obj) {
    this.messages = {}
    this.obj = "#"+obj
}
Manager.prototype.get = function (msg_id) {
    if (typeof(this.messages[msg_id]) == "undefined") {
        this.messages[msg_id] = new Message(msg_id, this.obj)
    }
    return this.messages[msg_id]
}
function Message(msg_id, obj) {
    this.num = exec_count
    $(obj).append("<div id='msg_"+msg_id+"' class='message'></div>")
    this.obj = $(obj+" #msg_"+msg_id)
    
    this.in_head = "<div class='input_header'>In [<span class='cbold'>"
    this.in_head += this.num+"</span>]:</div>"
    this.obj.append(this.in_head)
    this.in_head = $(obj+" #msg_"+msg_id +" .input_header")
    this.obj.append("<pre class='input'></pre><div class='clear'></div>")
    this.input = $(obj+" #msg_"+msg_id +" .input")
    
    this.out_head = "<div class='output_header'></div>"
    this.obj.append(this.out_head)
    this.out_head = $(obj+" #msg_"+msg_id +" .output_header")
    this.obj.append("<pre class='output'></pre><div class='clear'></div>")
    this.output = $(obj+" #msg_"+msg_id +" .output")
}
Message.prototype.setInput = function(value) {
    this.input.append(value)
}
Message.prototype.setOutput = function(value, header) {
    if (header) {
        var o = "Out [<span class='cbold'>"+this.num+"</span>]:"
        this.out_head.html(o)
    }
    this.output.append(value)
}
