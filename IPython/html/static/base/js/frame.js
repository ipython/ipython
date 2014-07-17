// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define(['base/js/utils'], function(utils) {
    "use strict";

    var FrameCommunicator = function (destination, is_iframe) {
        this.is_iframe = is_iframe;
        this.destination = destination;
        this.callbacks = {}; // id to callback
        this.msg_callback = null; // on_msg callbacks

        // Register message listener.
        var that = this;
        window.addEventListener('message', function(e){
            
            // TODO: check e.origin AND e.source
            // if (e.source != that.destination.contentWindow) {
            //     return;
            // }
            that._handle_msg(e.data.id, e.data.data);
        });
    };
    
    FrameCommunicator.prototype.send = function(msg, callback, id) {
        id = id || utils.uuid();
        if (callback) {
            this.callbacks[id] = callback;
        }

        var destination_window = this.destination;
        if (this.is_iframe) {
            destination_window = this.destination[0].contentWindow;
        }
        // TODO: Set * to the known origin.
        console.log('message out: ', msg);
        destination_window.postMessage({data: msg, id: id}, '*');
    };

    FrameCommunicator.prototype.on_msg = function(callback) {
        this.msg_callback = callback;
    };

    FrameCommunicator.prototype.off_msg = function(callback) {
        this.msg_callback = null;
    };

    FrameCommunicator.prototype._handle_msg = function(id, msg) {
        var that = this;
        console.log('message in : ', msg);
        var respond = function(response_msg, callback) {
            that.send(response_msg, callback, id);
        };

        // If a msg capturing callback is registered, call that instead of
        // calling the generic message handler.
        if (this.callbacks[id]) {
            this.callbacks[id](msg, respond);
            delete this.callbacks[id];
        } else if (this.msg_callback) {
            this.msg_callback(msg, respond);
        }
    };
    
    return {'FrameCommunicator': FrameCommunicator};
});
