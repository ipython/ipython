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

    var Kernel = function () {
        this.kernel_id = null;
        this.shell_channel = null;
        this.iopub_channel = null;
        this.base_url = $('body').data('baseKernelUrl') + "kernels";
        this.running = false;
        this.username = "username";
        this.session_id = utils.uuid();
        
        if (typeof(WebSocket) !== 'undefined') {
            this.WebSocket = WebSocket;
        } else if (typeof(MozWebSocket) !== 'undefined') {
            this.WebSocket = MozWebSocket;
        } else {
            alert('Your browser does not have WebSocket support, please try Chrome, Safari or Firefox ≥ 6. Firefox 4 and 5 are also supported by you have to enable WebSockets in about:config.');
        };
    };


    Kernel.prototype.get_msg = function (msg_type, content) {
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

    Kernel.prototype.start = function (notebook_id, callback) {
        var that = this;
        if (!this.running) {
            var qs = $.param({notebook:notebook_id});
            var url = this.base_url + '?' + qs;
            $.post(url,
                function (kernel_id) {
                    that._handle_start_kernel(kernel_id, callback);
                }, 
                'json'
            );
        };
    };


    Kernel.prototype.restart = function (callback) {
        IPython.kernel_status_widget.status_restarting();
        var url = this.kernel_url + "/restart";
        var that = this;
        if (this.running) {
            this.stop_channels();
            $.post(url,
                function (kernel_id) {
                    that._handle_start_kernel(kernel_id, callback);
                },
                'json'
            );
        };
    };


    Kernel.prototype._handle_start_kernel = function (json, callback) {
        this.running = true;
        this.kernel_id = json.kernel_id;
        this.ws_url = json.ws_url;
        this.kernel_url = this.base_url + "/" + this.kernel_id;
        this.start_channels();
        callback();
        IPython.kernel_status_widget.status_idle();
    };

    Kernel.prototype._websocket_closed = function(ws_url, early){
        var msg;
        var parent_item = $('body');
        if (early) {
            msg = "Websocket connection to " + ws_url + " could not be established.<br/>" +
            " You will NOT be able to run code.<br/>" +
            " Your browser may not be compatible with the websocket version in the server," +
            " or if the url does not look right, there could be an error in the" +
            " server's configuration.";
        } else {
            msg = "Websocket connection closed unexpectedly.<br/>" +
            " The kernel will no longer be responsive.";
        }
        var dialog = $('<div/>');
        dialog.html(msg);
        parent_item.append(dialog);
        dialog.dialog({
            resizable: false,
            modal: true,
            title: "Websocket closed",
            buttons : {
                "Okay": function () {
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

    Kernel.prototype.object_info_request = function (objname) {
        if(typeof(objname)!=null && objname!=null)
        {
            var content = {
                oname : objname.toString(),
            };
            var msg = this.get_msg("object_info_request", content);
            this.shell_channel.send(JSON.stringify(msg));
            return msg.header.msg_id;
        }
        return;
    }

    Kernel.prototype.execute = function (code) {
        var content = {
            code : code,
            silent : false,
            user_variables : [],
            user_expressions : {},
            allow_stdin : false
        };
        var msg = this.get_msg("execute_request", content);
        this.shell_channel.send(JSON.stringify(msg));
        return msg.header.msg_id;
    };


    Kernel.prototype.complete = function (line, cursor_pos) {
        var content = {
            text : '',
            line : line,
            cursor_pos : cursor_pos
        };
        var msg = this.get_msg("complete_request", content);
        this.shell_channel.send(JSON.stringify(msg));
        return msg.header.msg_id;
    };


    Kernel.prototype.interrupt = function () {
        if (this.running) {
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

    IPython.Kernel = Kernel;

    return IPython;

}(IPython));

