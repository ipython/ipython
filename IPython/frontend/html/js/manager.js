/***********************************************************************
 #-----------------------------------------------------------------------------
 # Copyright (c) 2010, IPython Development Team.
 #
 # Distributed under the terms of the Modified BSD License.
 #
 # The full license is in the file COPYING.txt, distributed with this software.
 #-----------------------------------------------------------------------------
 
 Manages messages that arrive via the CometGetter interface
 Creates new messages if required, otherwise manages the communication between
 COMET and the messages
 ***********************************************************************/

/***********************************************************************
 * Process any payload objects into html
 ***********************************************************************/
function procPayload(payload) {
    var data = null
    if (typeof(payload['format']) != "undefined") {
        var format = payload['format']
        if (format == "svg") {
            //Remove the doctype from the top, otherwise no way to embed
            data = payload['data'].split("\n").slice(4).join("\n")
        } else if (format == "png") {
            data = $(document.createElement("img"))
            data.attr("src", "data:image/png;"+payload['data'])
        }
    } else if (typeof(payload["text"]) != "undefined") {
        data = fixConsole(payload["text"])
    }
    
    return data
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
    
    this.buf_out = null
}
Manager.prototype.set = function (msg, msg_id) {
    msg.msg_id = msg_id
    if (this.ondeck == msg) {
        manager.messages[msg_id] = msg
        manager.ordering.push(msg)
        manager.ondeck = null
    } else {
        manager.messages[msg_id] = msg
    }
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
            this.ordering.length == 0)
            return this.get()
            
        return this.ordering[this.cursor]
    } else if (typeof(this.messages[msg_id]) == "undefined") {
        //Handle the manager.get(unknown) case, for messages from other clients
        if (this.ondeck != null)
            this.ondeck.remove()
        this.messages[msg_id] = new Message(msg_id, this.obj)
        this.ordering.push(this.messages[msg_id])
        if (this.ondeck != null) {
            this.ondeck = null
            this.get().activate()
        }
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
Manager.prototype.process = function (json, origin, immediate) {
    if (typeof(json.content.execution_count) != "undefined")
        exec_count = json.content.execution_count
        
    var id = json.parent_header.msg_id
    var type = json.msg_type
    var msg = this.get(id)
    var output = $(document.createElement("div"))
    var head = false
    
    if (type == "execute_reply") {
        if (json.content.payload.length > 0) {
            for (var i in json.content.payload)
                output.append(procPayload(json.content.payload[i]))
        }
        this.get().activate()
    } else if (type == "pyin") {
        if (json.content.code != "") {
            msg.setInput(json.content.code, true)
            kernhistory.append(json.content.code)
        }
    } else if (type == "stream") {
        output.append(fixConsole(json.content.data))
    } else if (type == "pyout") {
        exec_count = json.content.execution_count
        msg.num = json.content.execution_count
        output.append(fixConsole(json.content.data))
        head = true
    } else if (type == "pyerr") {
        output.append(fixConsole(json.content.traceback.join("\n")))
    }
    if (output.html() != "")
        msg.setOutput(output, head )
}
Manager.prototype.length = function () {
    return this.ordering.length
}
Manager.prototype.getOrder = function(msg) {
    for (var i = 0; i < this.ordering.length; i++)
        if (this.ordering[i] == msg)
            return i
    //If it's not found, it's probably ondeck, return the last element
    return this.ordering.length
}

