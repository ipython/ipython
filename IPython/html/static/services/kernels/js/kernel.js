// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

//============================================================================
// Kernel
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 * @submodule Kernel
 */

var IPython = (function (IPython) {
    "use strict";
    
    var utils = IPython.utils;

    // Initialization and connection.
    /**
     * A Kernel Class to communicate with the Python kernel
     * @Class Kernel
     */
    var Kernel = function (kernel_service_url) {
        this.kernel_id = null;
        this.shell_channel = null;
        this.iopub_channel = null;
        this.stdin_channel = null;
        this.kernel_service_url = kernel_service_url;
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
        }
        
        this.bind_events();
        this.init_iopub_handlers();
        this.comm_manager = new IPython.CommManager(this);
        this.widget_manager = new IPython.WidgetManager(this.comm_manager);
        
        this.last_msg_id = null;
        this.last_msg_callbacks = {};
    };


    Kernel.prototype._get_msg = function (msg_type, content, metadata) {
        var msg = {
            header : {
                msg_id : utils.uuid(),
                username : this.username,
                session : this.session_id,
                msg_type : msg_type
            },
            metadata : metadata || {},
            content : content,
            parent_header : {}
        };
        return msg;
    };
    
    Kernel.prototype.bind_events = function () {
        var that = this;
        $([IPython.events]).on('send_input_reply.Kernel', function(evt, data) { 
            that.send_input_reply(data);
        });
    };
    
    // Initialize the iopub handlers
    
    Kernel.prototype.init_iopub_handlers = function () {
        var output_types = ['stream', 'display_data', 'pyout', 'pyerr'];
        this._iopub_handlers = {};
        this.register_iopub_handler('status', $.proxy(this._handle_status_message, this));
        this.register_iopub_handler('clear_output', $.proxy(this._handle_clear_output, this));
        
        for (var i=0; i < output_types.length; i++) {
            this.register_iopub_handler(output_types[i], $.proxy(this._handle_output_message, this));
        }
    };

    /**
     * Start the Python kernel
     * @method start
     */
    Kernel.prototype.start = function (params) {
        params = params || {};
        if (!this.running) {
            var qs = $.param(params);
            $.post(utils.url_join_encode(this.kernel_service_url) + '?' + qs,
                $.proxy(this._kernel_started, this),
                'json'
            );
        }
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
        if (this.running) {
            this.stop_channels();
            $.post(utils.url_join_encode(this.kernel_url, "restart"),
                $.proxy(this._kernel_started, this),
                'json'
            );
        }
    };


    Kernel.prototype._kernel_started = function (json) {
        console.log("Kernel started: ", json.id);
        this.running = true;
        this.kernel_id = json.id;
        // trailing 's' in https will become wss for secure web sockets
        this.ws_host = location.protocol.replace('http', 'ws') + "//" + location.host;
        this.kernel_url = utils.url_path_join(this.kernel_service_url, this.kernel_id);
        this.start_channels();
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
        var ws_host_url = this.ws_host + this.kernel_url;
        console.log("Starting WebSockets:", ws_host_url);
        this.shell_channel = new this.WebSocket(
            this.ws_host + utils.url_join_encode(this.kernel_url, "shell")
        );
        this.stdin_channel = new this.WebSocket(
            this.ws_host + utils.url_join_encode(this.kernel_url, "stdin")
        );
        this.iopub_channel = new this.WebSocket(
            this.ws_host + utils.url_join_encode(this.kernel_url, "iopub")
        );
        
        var already_called_onclose = false; // only alert once
        var ws_closed_early = function(evt){
            if (already_called_onclose){
                return;
            }
            already_called_onclose = true;
            if ( ! evt.wasClean ){
                that._websocket_closed(ws_host_url, true);
            }
        };
        var ws_closed_late = function(evt){
            if (already_called_onclose){
                return;
            }
            already_called_onclose = true;
            if ( ! evt.wasClean ){
                that._websocket_closed(ws_host_url, false);
            }
        };
        var channels = [this.shell_channel, this.iopub_channel, this.stdin_channel];
        for (var i=0; i < channels.length; i++) {
            channels[i].onopen = $.proxy(this._ws_opened, this);
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
        this.iopub_channel.onmessage = $.proxy(this._handle_iopub_message, this);
        this.stdin_channel.onmessage = $.proxy(this._handle_input_request, this);
    };

    /**
     * Handle a websocket entering the open state
     * sends session and cookie authentication info as first message.
     * Once all sockets are open, signal the Kernel.status_started event.
     * @method _ws_opened
     */
    Kernel.prototype._ws_opened = function (evt) {
        // send the session id so the Session object Python-side
        // has the same identity
        evt.target.send(this.session_id + ':' + document.cookie);
        
        var channels = [this.shell_channel, this.iopub_channel, this.stdin_channel];
        for (var i=0; i < channels.length; i++) {
            // if any channel is not ready, don't trigger event.
            if ( !channels[i].readyState ) return;
        }
        // all events ready, trigger started event.
        $([IPython.events]).trigger('status_started.Kernel', {kernel: this});
    };
    
    /**
     * Stop the websocket channels.
     * @method stop_channels
     */
    Kernel.prototype.stop_channels = function () {
        var channels = [this.shell_channel, this.iopub_channel, this.stdin_channel];
        for (var i=0; i < channels.length; i++) {
            if ( channels[i] !== null ) {
                channels[i].onclose = null;
                channels[i].close();
            }
        }
        this.shell_channel = this.iopub_channel = this.stdin_channel = null;
    };

    // Main public methods.
    
    // send a message on the Kernel's shell channel
    Kernel.prototype.send_shell_message = function (msg_type, content, callbacks, metadata) {
        var msg = this._get_msg(msg_type, content, metadata);
        this.shell_channel.send(JSON.stringify(msg));
        this.set_callbacks_for_msg(msg.header.msg_id, callbacks);
        return msg.header.msg_id;
    };

    /**
     * Get kernel info
     *
     * @param callback {function}
     * @method object_info
     *
     * When calling this method, pass a callback function that expects one argument.
     * The callback will be passed the complete `kernel_info_reply` message documented
     * [here](http://ipython.org/ipython-doc/dev/development/messaging.html#kernel-info)
     */
    Kernel.prototype.kernel_info = function (callback) {
        var callbacks;
        if (callback) {
            callbacks = { shell : { reply : callback } };
        }
        return this.send_shell_message("kernel_info_request", {}, callbacks);
    };

    /**
     * Get info on an object
     *
     * @param objname {string}
     * @param callback {function}
     * @method object_info
     *
     * When calling this method, pass a callback function that expects one argument.
     * The callback will be passed the complete `object_info_reply` message documented
     * [here](http://ipython.org/ipython-doc/dev/development/messaging.html#object-information)
     */
    Kernel.prototype.object_info = function (objname, callback) {
        var callbacks;
        if (callback) {
            callbacks = { shell : { reply : callback } };
        }
        
        if (typeof(objname) !== null && objname !== null) {
            var content = {
                oname : objname.toString(),
                detail_level : 0,
            };
            return this.send_shell_message("object_info_request", content, callbacks);
        }
        return;
    };

    /**
     * Execute given code into kernel, and pass result to callback.
     *
     * @async
     * @method execute
     * @param {string} code
     * @param [callbacks] {Object} With the following keys (all optional)
     *      @param callbacks.shell.reply {function}
     *      @param callbacks.shell.payload.[payload_name] {function}
     *      @param callbacks.iopub.output {function}
     *      @param callbacks.iopub.clear_output {function}
     *      @param callbacks.input {function}
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
     *       shell : {
     *         reply : execute_reply_callback,
     *         payload : {
     *           set_next_input : set_next_input_callback,
     *         }
     *       },
     *       iopub : {
     *         output : output_callback,
     *         clear_output : clear_output_callback,
     *       },
     *       input : raw_input_callback
     *      }
     *
     * Each callback will be passed the entire message as a single arugment.
     * Payload handlers will be passed the corresponding payload and the execute_reply message.
     */
    Kernel.prototype.execute = function (code, callbacks, options) {

        var content = {
            code : code,
            silent : true,
            store_history : false,
            user_variables : [],
            user_expressions : {},
            allow_stdin : false
        };
        callbacks = callbacks || {};
        if (callbacks.input !== undefined) {
            content.allow_stdin = true;
        }
        $.extend(true, content, options);
        $([IPython.events]).trigger('execution_request.Kernel', {kernel: this, content:content});
        return this.send_shell_message("execute_request", content, callbacks);
    };

    /**
     * When calling this method, pass a function to be called with the `complete_reply` message
     * as its only argument when it arrives.
     *
     * `complete_reply` is documented
     * [here](http://ipython.org/ipython-doc/dev/development/messaging.html#complete)
     *
     * @method complete
     * @param line {integer}
     * @param cursor_pos {integer}
     * @param callback {function}
     *
     */
    Kernel.prototype.complete = function (line, cursor_pos, callback) {
        var callbacks;
        if (callback) {
            callbacks = { shell : { reply : callback } };
        }
        var content = {
            text : '',
            line : line,
            block : null,
            cursor_pos : cursor_pos
        };
        return this.send_shell_message("complete_request", content, callbacks);
    };


    Kernel.prototype.interrupt = function () {
        if (this.running) {
            $([IPython.events]).trigger('status_interrupting.Kernel', {kernel: this});
            $.post(utils.url_join_encode(this.kernel_url, "interrupt"));
        }
    };


    Kernel.prototype.kill = function () {
        if (this.running) {
            this.running = false;
            var settings = {
                cache : false,
                type : "DELETE",
                error : utils.log_ajax_error,
            };
            $.ajax(utils.url_join_encode(this.kernel_url), settings);
        }
    };

    Kernel.prototype.send_input_reply = function (input) {
        var content = {
            value : input,
        };
        $([IPython.events]).trigger('input_reply.Kernel', {kernel: this, content:content});
        var msg = this._get_msg("input_reply", content);
        this.stdin_channel.send(JSON.stringify(msg));
        return msg.header.msg_id;
    };


    // Reply handlers

    Kernel.prototype.register_iopub_handler = function (msg_type, callback) {
        this._iopub_handlers[msg_type] = callback;
    };

    Kernel.prototype.get_iopub_handler = function (msg_type) {
        // get iopub handler for a specific message type
        return this._iopub_handlers[msg_type];
    };


    Kernel.prototype.get_callbacks_for_msg = function (msg_id) {
        // get callbacks for a specific message
        if (msg_id == this.last_msg_id) {
            return this.last_msg_callbacks;
        } else {
            return this._msg_callbacks[msg_id];
        }
    };


    Kernel.prototype.clear_callbacks_for_msg = function (msg_id) {
        if (this._msg_callbacks[msg_id] !== undefined ) {
            delete this._msg_callbacks[msg_id];
        }
    };
    
    Kernel.prototype._finish_shell = function (msg_id) {
        var callbacks = this._msg_callbacks[msg_id];
        if (callbacks !== undefined) {
            callbacks.shell_done = true;
            if (callbacks.iopub_done) {
                this.clear_callbacks_for_msg(msg_id);
            }
        }
    };

    Kernel.prototype._finish_iopub = function (msg_id) {
        var callbacks = this._msg_callbacks[msg_id];
        if (callbacks !== undefined) {
            callbacks.iopub_done = true;
            if (callbacks.shell_done) {
                this.clear_callbacks_for_msg(msg_id);
            }
        }
    };
    
    /* Set callbacks for a particular message.
     * Callbacks should be a struct of the following form:
     * shell : {
     * 
     * }
    
     */
    Kernel.prototype.set_callbacks_for_msg = function (msg_id, callbacks) {
        this.last_msg_id = msg_id;
        if (callbacks) {
            // shallow-copy mapping, because we will modify it at the top level
            var cbcopy = this._msg_callbacks[msg_id] = this.last_msg_callbacks = {};
            cbcopy.shell = callbacks.shell;
            cbcopy.iopub = callbacks.iopub;
            cbcopy.input = callbacks.input;
            cbcopy.shell_done = (!callbacks.shell);
            cbcopy.iopub_done = (!callbacks.iopub);
        } else {
            this.last_msg_callbacks = {};
        }
    };


    Kernel.prototype._handle_shell_reply = function (e) {
        var reply = $.parseJSON(e.data);
        $([IPython.events]).trigger('shell_reply.Kernel', {kernel: this, reply:reply});
        var content = reply.content;
        var metadata = reply.metadata;
        var parent_id = reply.parent_header.msg_id;
        var callbacks = this.get_callbacks_for_msg(parent_id);
        if (!callbacks || !callbacks.shell) {
            return;
        }
        var shell_callbacks = callbacks.shell;
        
        // signal that shell callbacks are done
        this._finish_shell(parent_id);
        
        if (shell_callbacks.reply !== undefined) {
            shell_callbacks.reply(reply);
        }
        if (content.payload && shell_callbacks.payload) {
            this._handle_payloads(content.payload, shell_callbacks.payload, reply);
        }
    };


    Kernel.prototype._handle_payloads = function (payloads, payload_callbacks, msg) {
        var l = payloads.length;
        // Payloads are handled by triggering events because we don't want the Kernel
        // to depend on the Notebook or Pager classes.
        for (var i=0; i<l; i++) {
            var payload = payloads[i];
            var callback = payload_callbacks[payload.source];
            if (callback) {
                callback(payload, msg);
            }
        }
    };

    Kernel.prototype._handle_status_message = function (msg) {
        var execution_state = msg.content.execution_state;
        var parent_id = msg.parent_header.msg_id;
        
        // dispatch status msg callbacks, if any
        var callbacks = this.get_callbacks_for_msg(parent_id);
        if (callbacks && callbacks.iopub && callbacks.iopub.status) {
            try {
                callbacks.iopub.status(msg);
            } catch (e) {
                console.log("Exception in status msg handler", e, e.stack);
            }
        }
        
        if (execution_state === 'busy') {
            $([IPython.events]).trigger('status_busy.Kernel', {kernel: this});
        } else if (execution_state === 'idle') {
            // signal that iopub callbacks are (probably) done
            // async output may still arrive,
            // but only for the most recent request
            this._finish_iopub(parent_id);
            
            // trigger status_idle event
            $([IPython.events]).trigger('status_idle.Kernel', {kernel: this});
        } else if (execution_state === 'restarting') {
            // autorestarting is distinct from restarting,
            // in that it means the kernel died and the server is restarting it.
            // status_restarting sets the notification widget,
            // autorestart shows the more prominent dialog.
            $([IPython.events]).trigger('status_autorestarting.Kernel', {kernel: this});
            $([IPython.events]).trigger('status_restarting.Kernel', {kernel: this});
        } else if (execution_state === 'dead') {
            this.stop_channels();
            $([IPython.events]).trigger('status_dead.Kernel', {kernel: this});
        }
    };
    
    
    // handle clear_output message
    Kernel.prototype._handle_clear_output = function (msg) {
        var callbacks = this.get_callbacks_for_msg(msg.parent_header.msg_id);
        if (!callbacks || !callbacks.iopub) {
            return;
        }
        var callback = callbacks.iopub.clear_output;
        if (callback) {
            callback(msg);
        }
    };


    // handle an output message (pyout, display_data, etc.)
    Kernel.prototype._handle_output_message = function (msg) {
        var callbacks = this.get_callbacks_for_msg(msg.parent_header.msg_id);
        if (!callbacks || !callbacks.iopub) {
            return;
        }
        var callback = callbacks.iopub.output;
        if (callback) {
            callback(msg);
        }
    };

    // dispatch IOPub messages to respective handlers.
    // each message type should have a handler.
    Kernel.prototype._handle_iopub_message = function (e) {
        var msg = $.parseJSON(e.data);

        var handler = this.get_iopub_handler(msg.header.msg_type);
        if (handler !== undefined) {
            handler(msg);
        }
    };


    Kernel.prototype._handle_input_request = function (e) {
        var request = $.parseJSON(e.data);
        var header = request.header;
        var content = request.content;
        var metadata = request.metadata;
        var msg_type = header.msg_type;
        if (msg_type !== 'input_request') {
            console.log("Invalid input request!", request);
            return;
        }
        var callbacks = this.get_callbacks_for_msg(request.parent_header.msg_id);
        if (callbacks) {
            if (callbacks.input) {
                callbacks.input(request);
            }
        }
    };


    IPython.Kernel = Kernel;

    return IPython;

}(IPython));

