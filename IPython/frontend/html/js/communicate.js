function CometGetter() {
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
    this.process(json)
}
CometGetter.prototype.process = function (json) {
    var thisObj = this
    if (json.msg_type == "status") {
        statusbar.set(json.content.execution_state)
    } else if (this.pause) {
        setTimeout(function () { thisObj.process(json) }, 1)
    } else {
        manager.process(json)
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

function execute(code, msg) {
    comet.stop()
    $.ajax({
        type: "POST",
        data: {type:"execute", code:code},
        success: function(json, status, request) {
            comet.start()
            if (json != null) {
                manager.process(json, msg)
            }
        }
    })
}

function tabcomplete(code, pos, func) {
    $.ajax({
        type:"POST",
        data: {type:"complete", code:code, pos:pos},
        success: function(json, status, request) {
            func(json.content.matches)
        }
    })
}
