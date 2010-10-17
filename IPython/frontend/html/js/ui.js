/***********************************************************************
 * Tracks the status bar on the right, will eventually be draggable
 ***********************************************************************/
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
Manager.prototype.get = function (msg_id, sess) {
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
}
Message.prototype.deactivate = function () {
    this.outer.removeClass("active")
    this.input.html(this.code)
    this.active = false
}
Message.prototype.remove = function () {
    this.outer.remove()
    manager.ondeck = null
}
Message.prototype.setInput = function(value) {
    this.code = value
    this.input.html(value)
}
Message.prototype.setOutput = function(value, header) {
    this.in_head.html("In [<span class='cbold'>"+this.num+"</span>]:")
    this.output.html(value)
    if (header)
        this.out_head.html("Out [<span class='cbold'>"+this.num+"</span>]:")
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
            
            tabcomplete()
        }
    })
    $.scrollTo(this.text)
}
InputArea.prototype.submit = function (code) {
    this.msg.code = code
    comet.stop()
    var thisObj = this
    execute(code, function(json) {
        thisObj.msg.num = exec_count
        if (manager.ondeck == thisObj.msg)
            manager.set(json.parent_header.msg_id)
        else 
            manager.messages[json.parent_header.msg_id] = thisObj.msg
        comet.start()
    })
}
