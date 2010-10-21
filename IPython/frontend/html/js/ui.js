//Let's arbitrarily set the number of columns to 6
//We can eventually recompute the ideal width
columns = 6

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
    this.obj = $("#"+obj)
    this.history = []
//    gethistory(-1)
}
History.prototype.append = function(hist) {
    for (var i in hist) {
        this.history.push(hist[i])
        var obj = $(document.createElement("a"))
        obj.addClass("history_element")
        obj.attr("href", "javascript:kernhistory.click("+(this.history.length-1)+")")
        var code = hist[i].replace(/\n/g, "<br />")
        obj.html("["+i+"]: "+code)
        this.obj.append(obj)
    }
    this.obj.scrollTo(this.obj.children().last())
}
History.prototype.click = function (id) {
    var msg = manager.get()
    msg.code = this.history[id]
    msg.activate()
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
            throw Exception("Received other message with an origin??")
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
            msg.setOutput(msg.output.html()+fixConsole(json.content.data))
        } else if (type == "pyin") {
            if (json.content.code == "")
                msg.remove()
            else {
                var data = {}
                data[msg.num] = json.content.code
                msg.setInput(json.content.code, true)
                kernhistory.append(data)
            }
        } else if (type == "pyout") {
            exec_count = json.content.execution_count
            msg.num = json.content.execution_count
            msg.setOutput(msg.output.html()+fixConsole(json.content.data), true)
        } else if (type == "pyerr") {
            var data = fixConsole(json.content.traceback.join("\n"))
            msg.setOutput(msg.output.html() + data)
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
    this.in_head.html("In [<span class='cbold'>"+(exec_count+1)+"</span>]:")
    this.text = new InputArea(this)
    $.scrollTo(this.outer)
}
Message.prototype.deactivate = function () {
    this.in_head.html("In [<span class='cbold'>"+this.num+"</span>]:")
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
}
Message.prototype.setOutput = function(value, header) {
    var head = header?"Out [<span class='cbold'>"+this.num+"</span>]:":""
    this.out_head.html(head)
    this.output.html(value)
}

/***********************************************************************
 * Handles python input, submission, etc
 ***********************************************************************/
function InputArea(msg) {
    this.msg = msg
    this.activate()
}
InputArea.prototype.activate = function () {
    this.text = $(document.createElement("textarea")).val(this.msg.code)
    this.text.addClass("inputText")
    this.msg.input.html(this.text)
    this.lh = this.text.height()
    this.nlines = this.msg.code.split("\n").length
    this.update()
    
    var thisObj = this
    this.text.keydown(function (e) {thisObj.keyfunc(e)})
    this.text.keyup(function (e) {
        thisObj.msg.code = e.target.value
        thisObj.update() 
    })
    
    this.text.focus()
}
InputArea.prototype.keyfunc = function (e) {
    if (this.nlines > 1) {
        if (e.which == 13) {
            if (e.shiftKey)
                this.submit(e.target.value)
            else if (e.ctrlKey)
                this.text.val(this.text.val()+"\n")
        } 
    } else {
        if (e.which == 13) {
            if (e.ctrlKey) {
                this.text.val(this.text.val()+"\n")
            } else
                this.submit(e.target.value)
        } else if (e.which == 38) {
            manager.get("-1").activate()
        } else if (e.which == 40) {
            manager.get("+1").activate()
        } else if (e.which == 9) {
            e.preventDefault()
            var thisObj = this
            var pos = this.text.getSelection().end
            tabcomplete(this.text.val(), pos, 
                function(matches) {thisObj.complete(matches)}
            )
        }
    }
}
InputArea.prototype.update = function (nlines) {
    this.nlines = this.msg.code.split("\n").length + (nlines?nlines:0)
    this.text.animate({height: this.lh*(this.nlines) }, 100)
}
InputArea.prototype.submit = function (code) {
    this.msg.code = code
    if (code == "")
        this.msg.remove()
    else {
        this.msg.input.html(code)
        execute(code, this.msg)
    }
}
InputArea.prototype.complete = function (matches) {
    if (matches.length == 1)
        this.replace(matches[0])
    else if (matches.length > 1) {
        var pos = this.text.getSelection().end
        this.selector = new Selector(this, matches)
        var thisObj = this
        Selector.prototype.set = function (match) {
            thisObj.replace(match, pos)
            this.remove()
        }
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



function Selector(parent, matches) {
    this.parent = parent
    this.dialog = $(document.createElement("div"))
    this.dialog.addClass("completer")
    this.selectors = []
    this.cursor = 0
    
    this.pc = Math.ceil(matches.length / columns)
    for (var i = 0; i < columns; i++) {
        var column = $(document.createElement("div"))
        column.addClass("column")
        this.dialog.append(column)
        for (var j = 0; j < this.pc && i*this.pc+j < matches.length; j++) {
            var obj = new Selection(this, matches[i*this.pc+j], i*this.pc+j)
            this.selectors.push(obj)
            column.append(obj.obj)
            obj.init()
        }
    }
    
    var pos = this.parent.text.offset()
    pos.top += this.parent.text.height()
    this.dialog.offset(pos)
    $(document.body).append(this.dialog)
    this.selectors[this.cursor].active()
    
    var thisObj = this
    this.parent.text.unbind('keydown')
    this.parent.text.keydown(function (e) {
        var f = function () { e.preventDefault(); e.stopPropagation() }
        if (e.which == 37) {
            thisObj.next("-"); f()
        } else if (e.which == 38) {
            thisObj.next(-1); f()
        } else if (e.which == 39) {
            thisObj.next("+"); f()
        } else if (e.which == 40 || e.which == 9) {
            thisObj.next(1); f()
        } else if (e.which == 27) {
            thisObj.remove(); f()
        } else if (e.which == 13) {
            thisObj.set(thisObj.selectors[thisObj.cursor].match); f()
        } //Perhaps implement vim keys?
    })
    $(document).click(function (e){
        thisObj.remove();
    })
}
Selector.prototype.deselect = function () {
    for (var i in this.selectors)
        this.selectors[i].clear()
}
Selector.prototype.next = function (n) {
    if (n[0] == "+") {
        this.cursor += this.pc
    } else if (n[0] == "-") {
        this.cursor -= this.pc
    } else {
        this.cursor += n
    }
    this.cursor = mod(this.cursor, this.selectors.length)
    this.selectors[this.cursor].active()
}
Selector.prototype.remove = function () {
    this.dialog.remove()
    var parent = this.parent
    this.parent.text.unbind('keydown')
    this.parent.text.keydown(function (e) {parent.keyfunc(e)})
    this.parent.text.focus()
}


function Selection(parent, match, idx) {
    this.idx = idx
    this.parent = parent
    this.obj = $(document.createElement("div"))
    this.obj.addClass("selection")
    this.obj.html(match)
    this.match = match
}
Selection.prototype.init = function () {
    var thisObj = this
    this.obj.mouseover(function(e) { thisObj.active(); })
    this.obj.click(function (e) { 
        thisObj.parent.set(thisObj.match);
        thisObj.parent.remove()
        e.stopPropagation() 
    })
}
Selection.prototype.active = function () {
    this.parent.deselect()
    this.parent.cursor = this.idx
    this.obj.addClass("selected")
//    $.scrollTo(this.obj)
}
Selection.prototype.clear = function () {
    this.obj.removeClass("selected")
}
