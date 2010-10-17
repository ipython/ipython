function CometGetter() {
    this.start()
    this.request()
}
CometGetter.prototype.request = function () {
    var thisObj = this
    $.ajax({
        success: function (json, status, request) {
            thisObj.complete(json, status, request)
        }
    })
}
CometGetter.prototype.complete = function(json, status, request) {
    this.request()
    this.process(json)
}
CometGetter.prototype.process = function (json) {
    var thisObj = this
    if (json.msg_type == "status") {
        statusbar.set(json.content.execution_state)
    } else if (this.pause) {
        setTimeout(function () { thisObj.process(json) }, 10)
    } else {
        var msg = manager.get(
            json.parent_header.msg_id, 
            json.parent_header.session)
        if (json.msg_type == "stream") {
            msg.setOutput(fixConsole(json.content.data))
        } else if (json.msg_type == "pyin") {
            if (json.parent_header.session != session)
                msg.setInput(fixConsole(json.content.code))
        } else if (json.msg_type == "pyout") {
            exec_count = json.content.execution_count
            msg.num = json.content.execution_count
            msg.setOutput(fixConsole(json.content.data), true)
        } else if (json.msg_type == "pyerr") {
            msg.setOutput(fixConsole(json.content.traceback.join("\n")))
        }
    }
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
            setTimeout(heartbeat, 60000)
        }
    })
}

function execute(code, postfunc) {
    $.ajax({
        type: "POST",
        data: {type:"execute", code:code},
        success: function(json, status, request) {
            if (json != null) {
                exec_count = json.content.execution_count
                if (typeof(postfunc) != "undefined")
                    postfunc(json)
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
                //Open a new input object
                manager.get().activate()
            }
        }
    })
}

function complete() {
    
}
