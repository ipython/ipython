function CometGetter() {
    this.queue = []
    this.start()
    this.request()
}
CometGetter.prototype.request = function () {
    var thisObj = this
    $.ajax({
        success: function (json, status, request) {
            if (json != null)
                thisObj.complete(json, status, request)
        }, 
        error: function (request, status, error) {
            statusbar.set("dead")
        }
    })
}
CometGetter.prototype.complete = function(json, status, request) {
    this.request()
    if (json.msg_type == "status") {
        statusbar.set(json.content.execution_state)
    } else if (this.pause) {
        this.queue.push(json)
    } else {
        if (typeof(exec_count) != "undefined" || 
            json.msg_type == "execute_reply")
            manager.process(json, false, !this.pause)
    }
}
CometGetter.prototype.start = function () {
    this.pause = false
    while (this.queue.length > 0)
        manager.process(this.queue.pop())
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

function execute(code, msg) {
    comet.stop()
    if (code == "debug" || code == "%debug") {
        alert("REP socket not implemented yet, debug mode doesn't work")
        throw Exception("Not implemented yet")
    }
    $.ajax({
        type: "POST",
        data: {type:"execute", code:code},
        success: function(msg_id, status, request) {
            if (msg != null)
                manager.set(msg, msg_id)
            comet.start()
        }
    })
}

function tabcomplete(code, pos, callback) {
    $.ajax({
        type:"POST",
        data: {type:"complete", code:code, pos:pos},
        success: function(json, status, request) {
            callback(json.content.matches)
        }
    })
}
function gethistory(len) {
    $.ajax({
        type:"POST",
        data:{type:"history", index:len},
        success: function (json, status, request) {
            kernhistory.append(json.content.history)
        }
    })
}
