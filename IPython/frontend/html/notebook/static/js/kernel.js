//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Kernel
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    // Initialization and connection.

    var Kernel = function (base_url) {
        this.kernel_id = null;
        this.shell_channel = null;
        this.iopub_channel = null;
        this.base_url = base_url;
        this.running = false;
        this.username = "username";
        this.session_id = utils.uuid();
        this._msg_callbacks = {};

        if (typeof(WebSocket) !== 'undefined') {
            this.WebSocket = WebSocket;
        } else if (typeof(MozWebSocket) !== 'undefined') {
            this.WebSocket = MozWebSocket;
        } else {
            alert('Your browser does not have WebSocket support, please try Chrome, Safari or Firefox ≥ 6. Firefox 4 and 5 are also supported by you have to enable WebSockets in about:config.');
        };
    };


    Kernel.prototype._get_msg = function (msg_type, content) {
        var msg = {
            header : {
                msg_id : utils.uuid(),
                username : this.username,
                session : this.session_id,
                msg_type : msg_type
            },
            content : content,
            parent_header : {}
        };
        return msg;
    };

    Kernel.prototype.start = function (notebook_id) {
        var that = this;
        if (!this.running) {
            var qs = $.param({notebook:notebook_id});
            var url = this.base_url + '?' + qs;
            $.post(url,
                $.proxy(that._kernel_started,that),
                'json'
            );
        };
    };


    Kernel.prototype.restart = function () {
        $([IPython.events]).trigger('status_restarting.Kernel');
        var that = this;
        if (this.running) {
            this.stop_channels();
            var url = this.kernel_url + "/restart";
            $.post(url,
                $.proxy(that._kernel_started, that),
                'json'
            );
        };
    };


    Kernel.prototype._kernel_started = function (json) {
        console.log("Kernel started: ", json.kernel_id);
        this.running = true;
        this.kernel_id = json.kernel_id;
        this.ws_url = json.ws_url;
        this.kernel_url = this.base_url + "/" + this.kernel_id;
        this.start_channels();
        this.shell_channel.onmessage = $.proxy(this._handle_shell_reply,this);
        this.iopub_channel.onmessage = $.proxy(this._handle_iopub_reply,this);
    };


    Kernel.prototype._websocket_closed = function(ws_url, early){
        var msg;
        var parent_item = $('body');
        if (early) {
            msg = "Websocket connection to " + ws_url + " could not be established." +
            " You will NOT be able to run code." +
            " Your browser may not be compatible with the websocket version in the server," +
            " or if the url does not look right, there could be an error in the" +
            " server's configuration.";
        } else {
            IPython.notification_widget.set_message('Reconnecting Websockets', 1000);
            this.start_channels();
            return;
        }
        var dialog = $('<div/>');
        dialog.html(msg);
        parent_item.append(dialog);
        dialog.dialog({
            resizable: false,
            modal: true,
            title: "Websocket closed",
            closeText: "",
            close: function(event, ui) {$(this).dialog('destroy').remove();},
            buttons : {
                "OK": function () {
                    $(this).dialog('close');
                }
            }
        });

    };

    Kernel.prototype.start_channels = function () {
        var that = this;
        this.stop_channels();
        var ws_url = this.ws_url + this.kernel_url;
        console.log("Starting WS:", ws_url);
        this.shell_channel = new this.WebSocket(ws_url + "/shell");
        this.iopub_channel = new this.WebSocket(ws_url + "/iopub");
        send_cookie = function(){
            this.send(document.cookie);
        };
        var already_called_onclose = false; // only alert once
        ws_closed_early = function(evt){
            if (already_called_onclose){
                return;
            }
            already_called_onclose = true;
            if ( ! evt.wasClean ){
                that._websocket_closed(ws_url, true);
            }
        };
        ws_closed_late = function(evt){
            if (already_called_onclose){
                return;
            }
            already_called_onclose = true;
            if ( ! evt.wasClean ){
                that._websocket_closed(ws_url, false);
            }
        };
        this.shell_channel.onopen = send_cookie;
        this.shell_channel.onclose = ws_closed_early;
        this.iopub_channel.onopen = send_cookie;
        this.iopub_channel.onclose = ws_closed_early;
        // switch from early-close to late-close message after 1s
        setTimeout(function(){
            that.shell_channel.onclose = ws_closed_late;
            that.iopub_channel.onclose = ws_closed_late;
        }, 1000);
    };


    Kernel.prototype.stop_channels = function () {
        if (this.shell_channel !== null) {
            this.shell_channel.onclose = function (evt) {};
            this.shell_channel.close();
            this.shell_channel = null;
        };
        if (this.iopub_channel !== null) {
            this.iopub_channel.onclose = function (evt) {};
            this.iopub_channel.close();
            this.iopub_channel = null;
        };
    };

    // Main public methods.

    Kernel.prototype.object_info_request = function (objname, callbacks) {
        // When calling this method pass a callbacks structure of the form:
        //
        // callbacks = {
        //  'object_info_reply': object_into_reply_callback
        // }
        //
        // The object_info_reply_callback will be passed the content object of the
        // object_into_reply message documented here:
        //
        // http://ipython.org/ipython-doc/dev/development/messaging.html#object-information
        if(typeof(objname)!=null && objname!=null)
        {
            var content = {
                oname : objname.toString(),
            };
            var msg = this._get_msg("object_info_request", content);
            this.shell_channel.send(JSON.stringify(msg));
            this.set_callbacks_for_msg(msg.header.msg_id, callbacks);
            return msg.header.msg_id;
        }
        return;
    }

    Kernel.prototype.execute = function (code, callbacks, options) {
        // The options object should contain the options for the execute call. Its default
        // values are:
        //
        // options = {
        //   silent : true,
        //   user_variables : [],
        //   user_expressions : {},
        //   allow_stdin : false
        // }
        //
        // When calling this method pass a callbacks structure of the form:
        //
        // callbacks = {
        //  'execute_reply': execute_reply_callback,
        //  'output': output_callback,
        //  'clear_output': clear_output_callback,
        //  'set_next_input': set_next_input_callback
        // }
        //
        // The execute_reply_callback will be passed the content object of the execute_reply
        // message documented here:
        //
        // http://ipython.org/ipython-doc/dev/development/messaging.html#execute
        //
        // The output_callback will be passed msg_type ('stream','display_data','pyout','pyerr')
        // of the output and the content object of the PUB/SUB channel that contains the
        // output:
        //
        // http://ipython.org/ipython-doc/dev/development/messaging.html#messages-on-the-pub-sub-socket
        //
        // The clear_output_callback will be passed a content object that contains
        // stdout, stderr and other fields that are booleans.
        //
        // The set_next_input_callback will bepassed the text that should become the next
        // input cell.

        var content = {
            code : code,
            silent : true,
            user_variables : [],
            user_expressions : {},
            allow_stdin : false
        };
		$.extend(true, content, options)
        var msg = this._get_msg("execute_request", content);
        this.shell_channel.send(JSON.stringify(msg));
        this.set_callbacks_for_msg(msg.header.msg_id, callbacks);
        return msg.header.msg_id;
    };


    Kernel.prototype.complete = function (line, cursor_pos, callbacks) {
        // When calling this method pass a callbacks structure of the form:
        //
        // callbacks = {
        //  'complete_reply': complete_reply_callback
        // }
        //
        // The complete_reply_callback will be passed the content object of the
        // complete_reply message documented here:
        //
        // http://ipython.org/ipython-doc/dev/development/messaging.html#complete
        callbacks = callbacks || {};
        var content = {
            text : '',
            line : line,
            cursor_pos : cursor_pos
        };
        var msg = this._get_msg("complete_request", content);
        this.shell_channel.send(JSON.stringify(msg));
        this.set_callbacks_for_msg(msg.header.msg_id, callbacks);
        return msg.header.msg_id;
    };


    Kernel.prototype.interrupt = function () {
        if (this.running) {
            $([IPython.events]).trigger('status_interrupting.Kernel');
            $.post(this.kernel_url + "/interrupt");
        };
    };


    Kernel.prototype.kill = function () {
        if (this.running) {
            this.running = false;
            var settings = {
                cache : false,
                type : "DELETE"
            };
            $.ajax(this.kernel_url, settings);
        };
    };


    // Reply handlers.

    Kernel.prototype.get_callbacks_for_msg = function (msg_id) {
        var callbacks = this._msg_callbacks[msg_id];
        return callbacks;
    };


    Kernel.prototype.set_callbacks_for_msg = function (msg_id, callbacks) {
        this._msg_callbacks[msg_id] = callbacks || {};
    }


    Kernel.prototype._handle_shell_reply = function (e) {
        reply = $.parseJSON(e.data);
        var header = reply.header;
        var content = reply.content;
        var msg_type = header.msg_type;
        var callbacks = this.get_callbacks_for_msg(reply.parent_header.msg_id);
        if (callbacks !== undefined) {
            var cb = callbacks[msg_type];
            if (cb !== undefined) {
                cb(content);
            }
        };

        if (content.payload !== undefined) {
            var payload = content.payload || [];
            this._handle_payload(callbacks, payload);
        }
    };


    Kernel.prototype._handle_payload = function (callbacks, payload) {
        var l = payload.length;
        // Payloads are handled by triggering events because we don't want the Kernel
        // to depend on the Notebook or Pager classes.
        for (var i=0; i<l; i++) {
            if (payload[i].source === 'IPython.zmq.page.page') {
                var data = {'text':payload[i].text}
                $([IPython.events]).trigger('open_with_text.Pager', data);
            } else if (payload[i].source === 'IPython.zmq.zmqshell.ZMQInteractiveShell.set_next_input') {
                if (callbacks.set_next_input !== undefined) {
                    callbacks.set_next_input(payload[i].text)
                }
            }
        };
    };


    Kernel.prototype._handle_iopub_reply = function (e) {
        reply = $.parseJSON(e.data);
        var content = reply.content;
        var msg_type = reply.header.msg_type;
        var callbacks = this.get_callbacks_for_msg(reply.parent_header.msg_id);
        if (msg_type !== 'status' && callbacks === undefined) {
            // Message not from one of this notebook's cells and there are no
            // callbacks to handle it.
            return;
        }
        var output_types = ['stream','display_data','pyout','pyerr'];
        if (output_types.indexOf(msg_type) >= 0) {
            var cb = callbacks['output'];
            if (cb !== undefined) {
                cb(msg_type, content);
            }
        } else if (msg_type === 'status') {
            if (content.execution_state === 'busy') {
                $([IPython.events]).trigger('status_busy.Kernel');
            } else if (content.execution_state === 'idle') {
                $([IPython.events]).trigger('status_idle.Kernel');
            } else if (content.execution_state === 'dead') {
                this.stop_channels();
                $([IPython.events]).trigger('status_dead.Kernel');
            };
        } else if (msg_type === 'clear_output') {
            var cb = callbacks['clear_output'];
            if (cb !== undefined) {
                cb(content);
            }
        };
    };


    IPython.Kernel = Kernel;

    return IPython;

}(IPython));

