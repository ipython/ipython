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

function CometGetter() {
    this.start()
    this.request()
}
CometGetter.prototype.complete = function(json, status, request) {
    this.request()
//$("#messages").append("<pre class='headers'>"+json.msg_type+": "+inspect(json.header)+inspect(json.parent_header)+"</pre>")
    this.process(json)
}
CometGetter.prototype.process = function (json) {
    var thisObj = this
    if (json.msg_type == "status") {
        statusbar.set(json.content.execution_state)
    } else if (this.pause) {
        setTimeout(function () { thisObj.process(json) }, 10)
    } else {
        var msg = manager.get(json.parent_header.msg_id, json.parent_header.session)
        if (json.msg_type == "stream") {
            msg.setOutput(fixConsole(json.content.data))
        } else if (json.msg_type == "pyin") {
            if (json.parent_header.session != session)
                msg.setInput(fixConsole(json.content.code))
        } else if (json.msg_type == "pyout") {
            msg.setOutput(fixConsole(json.content.data), true)
        } else if (json.msg_type == "pyerr") {
            msg.setOutput(fixConsole(json.content.traceback.join("\n")))
        }
    }
}
CometGetter.prototype.request = function () {
    var thisObj = this
    $.ajax({
        success: function (json, status, request) {
            thisObj.complete(json, status, request)
        }
    })
}
CometGetter.prototype.start = function () {
    this.pause = false
}
CometGetter.prototype.stop = function () {
    this.pause = true
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
function execute(code, postfunc) {
    $.ajax({
        type: "POST",
        data: {type:"execute", code:code},
        success: function(json, status, request) {
            if (typeof(postfunc) != "undefined")
                postfunc(json)
            if (json != null) {
//$("#messages").append("<pre class='headers'>"+json.msg_type+": "+inspect(json.header)+inspect(json.parent_header)+"</pre>")
                exec_count = json.content.execution_count
                if (json.content.payload.length > 0 && 
                    json.content.payload[0]['format'] == "svg") {
                    var svg = document.createElement('object')
                    svg.setAttribute('class', "inlinesvg")
                    svg.setAttribute('type', 'image/svg+xml')
                    svg.setAttribute('data', 'data:image/svg+xml,'+ 
                        json.content.payload[0]['data'])              
                    manager.get(json.parent_header.msg_id).setOutput(svg)
                    manager.get(json.parent_header.msg_id).setOutput("<br />")
                }
            }
            //Open a new input object
            manager.get().activate()
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
    this.ordering = []
    this.obj = "#"+obj
    this.ondeck = null
}
Manager.prototype.get = function (msg_id, sess) {
    if (typeof(msg_id) == "undefined") {
        if (this.ondeck == null)
            this.ondeck = new Message(-1, this.obj)
        return this.ondeck
    } else if (typeof(this.messages[msg_id]) == "undefined") {
        if (sess != session) {
            if (this.ondeck != null)
                this.ondeck.remove()
            this.messages[msg_id] = new Message(msg_id, this.obj)
            this.ordering.push(this.messages[msg_id])
            this.get().activate()
        }
    }
    return this.messages[msg_id]
}
Manager.prototype.set = function (msg_id) {
    if (this.ondeck == null)
        alert("Error, nothing ondeck!")
    else {
        this.messages[msg_id] = this.ondeck
        this.ordering.push(this.ondeck)
        this.ondeck = null
    }
}
Manager.prototype.order = function (idx) {
    idx = idx<0?this.ordering.length+idx:idx
    return this.ordering[idx]
}

function Message(msg_id, obj) {
    this.num = msg_id == -1?exec_count+1:exec_count
    this.obj = $(document.createElement("div"))
    this.obj.addClass("message")
    $(obj).append(this.obj)
    this.active = false
    
    this.in_head = $(document.createElement("div"))
    this.in_head.addClass("input_header")
    this.in_head.html("In [<span class='cbold'>"+this.num+"</span>]:")
    this.obj.append(this.in_head)
    
    this.input = $(document.createElement("pre"))
    this.input.addClass("input")
    this.obj.append(this.input)
    this.obj.append("<div class='clear'></div>")
    
    this.out_head = $(document.createElement("div"))
    this.out_head.addClass("output_header")
    this.obj.append(this.out_head)
    
    this.output = $(document.createElement("pre"))
    this.output.addClass("output")
    this.obj.append(this.output)
    this.obj.append("<div class='clear'></div>")
}
Message.prototype.activate = function () {
    this.active = true
    var input = document.createElement("input")
    input.setAttribute("value", this.input.text().replace("'", "\\'"))
    this.text = $(input)
    this.input.html(this.text)
    this.text.focus()
    
    var thisObj = this
    this.text.keypress(function(e) {
        if (e.which == 13)
            thisObj.submit(e.target.value)
    })
}
Message.prototype.submit = function (code) {
    var thisObj = this
    this.input.html(code)
    comet.stop()
    execute(code, function(json) {
        thisObj.active = false
        manager.set(json.parent_header.msg_id)
        comet.start()
    })
}
Message.prototype.remove = function () {
    this.obj.remove()
    manager.ondeck = null
}
Message.prototype.setInput = function(value) {
    this.input.html(value)
}
Message.prototype.setOutput = function(value, header) {
    if (header) {
        var o = "Out [<span class='cbold'>"+this.num+"</span>]:"
        this.out_head.html(o)
    }
    this.output.append(value)
}
