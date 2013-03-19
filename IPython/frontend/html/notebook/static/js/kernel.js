//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Kernel
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 * @submodule Kernel
 */

var IPython = (function (IPython) {

    var utils = IPython.utils;

    // Initialization and connection.
    /**
     * A Kernel Class to communicate with the Python kernel
     * @Class Kernel
     */
    var Kernel = function (base_url) {
        this.kernel_id = null;
        this.shell_channel = null;
        this.iopub_channel = null;
        this.stdin_channel = null;
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
            metadata : {},
            content : content,
            parent_header : {}
        };
        return msg;
    };

    /**
     * Start the Python kernel
     * @method start
     */
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

    /**
     * Restart the python kernel.
     *
     * Emit a 'status_restarting.Kernel' event with
     * the current object as parameter
     *
     * @method restart
     */
    Kernel.prototype.restart = function () {
        $([IPython.events]).trigger('status_restarting.Kernel', {kernel: this});
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
        $([IPython.events]).trigger('status_started.Kernel', {kernel: this});
    };


    Kernel.prototype._websocket_closed = function(ws_url, early) {
        this.stop_channels();
        $([IPython.events]).trigger('websocket_closed.Kernel', 
            {ws_url: ws_url, kernel: this, early: early}
        );
    };

    /**
     * Start the `shell`and `iopub` channels.
     * Will stop and restart them if they already exist.
     *
     * @method start_channels
     */
    Kernel.prototype.start_channels = function () {
        var that = this;
        this.stop_channels();
        var ws_url = this.ws_url + this.kernel_url;
        console.log("Starting WebSockets:", ws_url);
        this.shell_channel = new this.WebSocket(ws_url + "/shell");
        this.stdin_channel = new this.WebSocket(ws_url + "/stdin");
        this.iopub_channel = new this.WebSocket(ws_url + "/iopub");
        send_cookie = function(){
            this.send(that.session_id + ':' + document.cookie);
        };
        var already_called_onclose = false; // only alert once
        var ws_closed_early = function(evt){
            if (already_called_onclose){
                return;
            }
            already_called_onclose = true;
            if ( ! evt.wasClean ){
                that._websocket_closed(ws_url, true);
            }
        };
        var ws_closed_late = function(evt){
            if (already_called_onclose){
                return;
            }
            already_called_onclose = true;
            if ( ! evt.wasClean ){
                that._websocket_closed(ws_url, false);
            }
        };
        var channels = [this.shell_channel, this.iopub_channel, this.stdin_channel];
        for (var i=0; i < channels.length; i++) {
            channels[i].onopen = send_cookie;
            channels[i].onclose = ws_closed_early;
        }
        // switch from early-close to late-close message after 1s
        setTimeout(function() {
            for (var i=0; i < channels.length; i++) {
                if (channels[i] !== null) {
                    channels[i].onclose = ws_closed_late;
                }
            }
        }, 1000);
        this.shell_channel.onmessage = $.proxy(this._handle_shell_reply, this);
        this.iopub_channel.onmessage = $.proxy(this._handle_iopub_reply, this);
        this.stdin_channel.onmessage = $.proxy(this._handle_input_request, this);
    };

    /**
     * Start the `shell`and `iopub` channels.
     * @method stop_channels
     */
    Kernel.prototype.stop_channels = function () {
        var channels = [this.shell_channel, this.iopub_channel, this.stdin_channel];
        for (var i=0; i < channels.length; i++) {
            if ( channels[i] !== null ) {
                channels[i].onclose = function (evt) {};
                channels[i].close();
            }
        };
        this.shell_channel = this.iopub_channel = this.stdin_channel = null;
    };

    // Main public methods.

    /**
     * Get info on object asynchronoulsy
     *
     * @async
     * @param objname {string}
     * @param callback {dict}
     * @method object_info_request
     *
     * @example
     *
     * When calling this method pass a callbacks structure of the form:
     *
     *     callbacks = {
     *      'object_info_reply': object_info_reply_callback
     *     }
     *
     * The `object_info_reply_callback` will be passed the content object of the
     *
     * `object_into_reply` message documented in
     * [IPython dev documentation](http://ipython.org/ipython-doc/dev/development/messaging.html#object-information)
     */
    Kernel.prototype.object_info_request = function (objname, callbacks) {
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

    /**
     * Execute given code into kernel, and pass result to callback.
     *
     * @async
     * @method execute
     * @param {string} code
     * @param callback {Object} With the following keys
     *      @param callback.'execute_reply' {function}
     *      @param callback.'output' {function}
     *      @param callback.'clear_output' {function}
     *      @param callback.'set_next_input' {function}
     * @param {object} [options]
     *      @param [options.silent=false] {Boolean}
     *      @param [options.user_expressions=empty_dict] {Dict}
     *      @param [options.user_variables=empty_list] {List od Strings}
     *      @param [options.allow_stdin=false] {Boolean} true|false
     *
     * @example
     *
     * The options object should contain the options for the execute call. Its default
     * values are:
     *
     *      options = {
     *        silent : true,
     *        user_variables : [],
     *        user_expressions : {},
     *        allow_stdin : false
     *      }
     *
     * When calling this method pass a callbacks structure of the form:
     *
     *      callbacks = {
     *       'execute_reply': execute_reply_callback,
     *       'output': output_callback,
     *       'clear_output': clear_output_callback,
     *       'set_next_input': set_next_input_callback
     *      }
     *
     * The `execute_reply_callback` will be passed the content and metadata
     * objects of the `execute_reply` message documented
     * [here](http://ipython.org/ipython-doc/dev/development/messaging.html#execute)
     *
     * The `output_callback` will be passed `msg_type` ('stream','display_data','pyout','pyerr')
     * of the output and the content and metadata objects of the PUB/SUB channel that contains the
     * output:
     *
     * http://ipython.org/ipython-doc/dev/development/messaging.html#messages-on-the-pub-sub-socket
     *
     * The `clear_output_callback` will be passed a content object that contains
     * stdout, stderr and other fields that are booleans, as well as the metadata object.
     *
     * The `set_next_input_callback` will be passed the text that should become the next
     * input cell.
     */
    Kernel.prototype.execute = function (code, callbacks, options) {

        var content = {
            code : code,
            silent : true,
            user_variables : [],
            user_expressions : {},
            allow_stdin : true
        };
        $.extend(true, content, options)
        $([IPython.events]).trigger('execution_request.Kernel', {kernel: this, content:content});
        var msg = this._get_msg("execute_request", content);
        this.shell_channel.send(JSON.stringify(msg));
        this.set_callbacks_for_msg(msg.header.msg_id, callbacks);
        return msg.header.msg_id;
    };

    /**
     * When calling this method pass a callbacks structure of the form:
     *
     *      callbacks = {
     *       'complete_reply': complete_reply_callback
     *      }
     *
     * The `complete_reply_callback` will be passed the content object of the
     * `complete_reply` message documented
     * [here](http://ipython.org/ipython-doc/dev/development/messaging.html#complete)
     *
     * @method complete
     * @param line {integer}
     * @param cursor_pos {integer}
     * @param {dict} callbacks
     *      @param callbacks.complete_reply {function} `complete_reply_callback`
     *
     */
    Kernel.prototype.complete = function (line, cursor_pos, callbacks) {
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
            $([IPython.events]).trigger('status_interrupting.Kernel', {kernel: this});
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

    Kernel.prototype.send_input_reply = function (input, header) {

        var content = {
            value : input,
        };
        $([IPython.events]).trigger('input_reply.Kernel', {kernel: this, content:content});
        var msg = this._get_msg("input_reply", content);
        this.stdin_channel.send(JSON.stringify(msg));
        return msg.header.msg_id;
    };


    // Reply handlers

    Kernel.prototype.get_callbacks_for_msg = function (msg_id) {
        var callbacks = this._msg_callbacks[msg_id];
        return callbacks;
    };


    Kernel.prototype.set_callbacks_for_msg = function (msg_id, callbacks) {
        this._msg_callbacks[msg_id] = callbacks || {};
    }


    Kernel.prototype._handle_shell_reply = function (e) {
        var reply = $.parseJSON(e.data);
        $([IPython.events]).trigger('shell_reply.Kernel', {kernel: this, reply:reply});
        var header = reply.header;
        var content = reply.content;
        var metadata = reply.metadata;
        var msg_type = header.msg_type;
        var callbacks = this.get_callbacks_for_msg(reply.parent_header.msg_id);
        if (callbacks !== undefined) {
            var cb = callbacks[msg_type];
            if (cb !== undefined) {
                cb(content, metadata);
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
            if (payload[i].source === 'IPython.kernel.zmq.page.page') {
                var data = {'text':payload[i].text}
                $([IPython.events]).trigger('open_with_text.Pager', data);
            } else if (payload[i].source === 'IPython.kernel.zmq.zmqshell.ZMQInteractiveShell.set_next_input') {
                if (callbacks.set_next_input !== undefined) {
                    callbacks.set_next_input(payload[i].text)
                }
            }
        };
    };


    Kernel.prototype._handle_iopub_reply = function (e) {
        var reply = $.parseJSON(e.data);
        var content = reply.content;
        var msg_type = reply.header.msg_type;
        var metadata = reply.metadata;
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
                cb(msg_type, content, metadata);
            }
        } else if (msg_type === 'status') {
            if (content.execution_state === 'busy') {
                $([IPython.events]).trigger('status_busy.Kernel', {kernel: this});
            } else if (content.execution_state === 'idle') {
                $([IPython.events]).trigger('status_idle.Kernel', {kernel: this});
            } else if (content.execution_state === 'restarting') {
                $([IPython.events]).trigger('status_restarting.Kernel', {kernel: this});
            } else if (content.execution_state === 'dead') {
                this.stop_channels();
                $([IPython.events]).trigger('status_dead.Kernel', {kernel: this});
            };
        } else if (msg_type === 'clear_output') {
            var cb = callbacks['clear_output'];
            if (cb !== undefined) {
                cb(content, metadata);
            }
        };
    };


    Kernel.prototype._handle_input_request = function (e) {
        var request = $.parseJSON(e.data);
        console.log("input", request);
        var header = request.header;
        var content = request.content;
        var metadata = request.metadata;
        var msg_type = header.msg_type;
        if (msg_type !== 'input_request') {
            console.log("Invalid input request!", request);
            return;
        }
        $([IPython.events]).trigger('input_request.Kernel', {kernel: this, request:request});
    };


    IPython.Kernel = Kernel;

    return IPython;

}(IPython));

