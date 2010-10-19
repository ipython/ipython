/***********************************************************************
 * Tracks the status bar on the right, will eventually be draggable
 ***********************************************************************/
function StatusBar(obj) {
    this.text = $(document.createElement("span"))
    this.text.addClass("txt")
    $("#"+obj).append(this.text)
    this.bullet = $(document.createElement("span"))
    this.bullet.addClass("bullet")
    this.bullet.html("&#8226;")
    $("#"+obj).append(this.bullet)
}
StatusBar.prototype.map = { "idle":"cgreen", "busy":"cyellow", "dead":"cred" }
StatusBar.prototype.set = function(status) {
    this.bullet.removeClass()
    this.bullet.addClass("bullet "+this.map[status])
    this.text.text(status)
}

function History(obj) {
    this.obj = $(obj)
//    gethistory(-1)
}
History.prototype.append = function(hist) {
    for (var i in hist) {
        var obj = $(document.createElement("div"))
        obj.addClass("history_element")
        obj.html("["+i+"]: "+hist[i])
        this.obj.append(obj)
    }
}

/***********************************************************************
 * Manages the messages and their ordering
 ***********************************************************************/
function Manager(obj) {
    this.messages = {}
    this.ordering = []
    this.obj = "#"+obj
    this.ondeck = null
    this.cursor = 0
    var thisObj = this
    $(document).click(function() {
        thisObj.deactivate(thisObj.ondeck)
    })
}
Manager.prototype.get = function (msg_id) {
    if (typeof(msg_id) == "undefined") {
        //Handle manager.get(), to return a new message on deck
        if (this.ondeck == null) {
            this.ondeck = new Message(-1, this.obj)
            this.cursor = this.ordering.length
        }
        return this.ondeck
    } else if (msg_id[0] == "+" || msg_id[0] == "-") {
        //Handle the manager.get("+1") case, to advance the cursor
        var idx = parseInt(msg_id)
        if (this.cursor + idx <= this.ordering.length &&
            this.cursor + idx >= 0)
            this.cursor += idx
        if (this.cursor >= this.ordering.length ||
            this.ordering.length == 0) {
            return this.get()
        }
        return this.ordering[this.cursor]
    } else if (typeof(this.messages[msg_id]) == "undefined") {
        this.messages[msg_id] = new Message(msg_id, this.obj)
        this.ordering.push(this.messages[msg_id])
    }
    return this.messages[msg_id]
}
Manager.prototype.deactivate = function (current) {
    for (var i in this.messages)
        this.messages[i].deactivate()
    if (this.ondeck != null) {
        this.ondeck.deactivate()
        if (this.ondeck != current) { 
            this.ondeck.remove()
            this.ondeck = null
        }
    }
}
Manager.prototype.process = function (json, origin) {
    var id = json.parent_header.msg_id
    var type = json.msg_type
    
    if (typeof(origin) != "undefined") {
        if (type != "execute_reply") 
            throw Exception("Recieved other message with an origin??")
        this.messages[id] = origin
        if (origin == this.ondeck) { 
            this.ordering.push(origin)
            this.ondeck = null
        }
    }
    
    var msg = this.get(id)
    if (type == "execute_reply") {
        exec_count = json.content.execution_count
        //If this reply has an SVG, let's add it
        if (json.content.payload.length > 0) {
            var payload = json.content.payload[0]
            if (typeof(payload['format']) != "undefined") {
                var format = payload['format']
                if (format == "svg") {
                    var data = payload['data']
                    //Remove the doctype from the top, otherwise no way to embed
                    data = data.split("\n").slice(4).join("\n")
                    var svg = document.createElement("div")
                    svg.innerHTML = data
                    msg.setOutput(svg)
                } else if (format == "png") {
                    var png = document.createElement("img")
                    png.src = "data:image/png;"+payload['data']
                    msg.setOutput(png)
                }
            } else if (typeof(payload["text"]) != "undefined") {
                msg.setOutput(fixConsole(payload["text"]))
            }
        } else {
            msg.setOutput("")
        }
        //Open a new input object
        manager.get().activate()
    } else {
        var removed = false
        if (this.ondeck != null && this.ondeck.code == "") {
            this.ondeck.remove()
            removed = true
        }
        if (type == "stream") {
            msg.setOutput(fixConsole(json.content.data))
        } else if (type == "pyin") {
            if (json.content.code == "")
                msg.remove()
            else
                msg.setInput(json.content.code, true)
        } else if (type == "pyout") {
            exec_count = json.content.execution_count
            msg.num = json.content.execution_count
            msg.setOutput(msg.output.html() + fixConsole(json.content.data), true)
        } else if (type == "pyerr") {
            msg.setOutput(fixConsole(json.content.traceback.join("\n")))
        }
        if (removed) this.get().activate()
    }
    
    if (typeof(origin) != "undefined")
        origin.msg_id = id
}
Manager.prototype.length = function () {
    return this.ordering.length
}

/***********************************************************************
 * Each message is a paired input/output object
 ***********************************************************************/
function Message(msg_id, obj) {
    this.msg_id = msg_id
    this.num = msg_id == -1?exec_count+1:exec_count
    
    this.outer = $(document.createElement("div"))
    this.outer.addClass("message")
    $(obj).append(this.outer)
    this.obj = $(document.createElement("div"))
    this.obj.addClass("message_inside")
    this.outer.append(this.obj)
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
    
    this.code = ""
    var thisObj = this
    this.obj.click(function(e) {
        thisObj.activate()
        e.stopPropagation()
    })
}
Message.prototype.activate = function () {
    this.active = true
    manager.deactivate(this)
    this.outer.addClass("active")
    this.text = new InputArea(this)
    $.scrollTo(this.outer)
}
Message.prototype.deactivate = function () {
    this.outer.removeClass("active")
    this.input.html(this.code)
    this.active = false
}
Message.prototype.remove = function () {
    this.outer.remove()
    if (manager.ondeck == this)
        manager.ondeck = null
}
Message.prototype.setInput = function(value, header) {
    this.code = value
    this.input.html(value)
    var head = header?"In [<span class='cbold'>"+this.num+"</span>]:":""
    this.in_head.html(head)
}
Message.prototype.setOutput = function(value, header) {
    this.output.html(value)
    var head = header?"Out [<span class='cbold'>"+this.num+"</span>]:":""
    this.out_head.html(head)
}

/***********************************************************************
 * Handles python input, including autocompletion, submission, etc
 ***********************************************************************/
function InputArea(msg) {
    this.msg = msg
    this.activate()
}
InputArea.prototype.activate = function () {
    var input = document.createElement("input")
    input.setAttribute("value", this.msg.code)
    this.text = $(input)
    this.msg.input.html(this.text)
    this.text.focus()
    
    var thisObj = this
    this.text.keydown(function(e) {
        if (e.which == 13)
            thisObj.submit(e.target.value)
        else if (e.which == 38) {
            manager.get("-1").activate()
        } else if (e.which == 40) {
            manager.get("+1").activate()
        } else if (e.which == 9) {
            e.preventDefault()
            var pos = thisObj.text.getSelection().end
            tabcomplete(thisObj.text.get(0).value, pos, function(matches) {
                thisObj.complete(matches)
            })
        } else {
            thisObj.msg.code = e.target.value
        }
    })
}
InputArea.prototype.submit = function (code) {
    this.msg.code = code
    if (code == "")
        this.msg.remove()
    else 
        execute(code, this.msg)
}
InputArea.prototype.complete = function (matches) {
    if (matches.length == 1)
        this.replace(matches[0])
    else if (matches.length > 1) {
        //TODO:Implement a multi-selector!
        var pos = this.text.getSelection().end
        
    }
}
InputArea.prototype.replace = function (match, pos) {
    if (typeof(pos) == "undefined")
        pos = this.text.getSelection().end
    var code = this.text.val()
    var words = code.slice(0,pos).split(' ')
    var end = code.slice(pos)
    words[words.length-1] = match
    if (end.length > 0)
        words.push(end)
    this.msg.code = words.join(' ')
    this.text.val(this.msg.code)
}
