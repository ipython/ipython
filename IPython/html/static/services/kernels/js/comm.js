//----------------------------------------------------------------------------
//  Copyright (C) 2013  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Comm and CommManager bases
//============================================================================
/**
 * Base Comm classes
 * @module IPython
 * @namespace IPython
 * @submodule comm
 */

var IPython = (function (IPython) {
    "use strict";

    //-----------------------------------------------------------------------
    // CommManager class
    //-----------------------------------------------------------------------
    
    var CommManager = function (kernel) {
        this.comms = {};
        this.targets = {};
        if (kernel !== undefined) {
            this.init_kernel(kernel);
        }
    };
    
    CommManager.prototype.init_kernel = function (kernel) {
        // connect the kernel, and register message handlers
        this.kernel = kernel;
        var msg_types = ['comm_open', 'comm_msg', 'comm_close'];
        for (var i = 0; i < msg_types.length; i++) {
            var msg_type = msg_types[i];
            kernel.register_iopub_handler(msg_type, $.proxy(this[msg_type], this));
        }
    };
    
    CommManager.prototype.new_comm = function (target_name, data, callbacks, metadata) {
        // Create a new Comm, register it, and open its Kernel-side counterpart
        // Mimics the auto-registration in `Comm.__init__` in the IPython Comm
        var comm = new Comm(target_name);
        this.register_comm(comm);
        comm.open(data, callbacks, metadata);
        return comm;
    };
    
    CommManager.prototype.register_target = function (target_name, f) {
        // Register a target function for a given target name
        this.targets[target_name] = f;
    };
    
    CommManager.prototype.unregister_target = function (target_name, f) {
        // Unregister a target function for a given target name
        delete this.targets[target_name];
    };
    
    CommManager.prototype.register_comm = function (comm) {
        // Register a comm in the mapping
        this.comms[comm.comm_id] = comm;
        comm.kernel = this.kernel;
        return comm.comm_id;
    };
    
    CommManager.prototype.unregister_comm = function (comm_id) {
        // Remove a comm from the mapping
        delete this.comms[comm_id];
    };
    
    // comm message handlers
    
    CommManager.prototype.comm_open = function (msg) {
        var content = msg.content;
        var f = this.targets[content.target_name];
        if (f === undefined) {
            console.log("No such target registered: ", content.target_name);
            console.log("Available targets are: ", this.targets);
            return;
        }
        var comm = new Comm(content.target_name, content.comm_id);
        this.register_comm(comm);
        try {
            f(comm, msg);
        } catch (e) {
            console.log("Exception opening new comm:", e, e.stack, msg);
            comm.close();
            this.unregister_comm(comm);
        }
    };
    
    CommManager.prototype.comm_close = function (msg) {
        var content = msg.content;
        var comm = this.comms[content.comm_id];
        if (comm === undefined) {
            return;
        }
        delete this.comms[content.comm_id];
        try {
            comm.handle_close(msg);
        } catch (e) {
            console.log("Exception closing comm: ", e, e.stack, msg);
        }
    };
    
    CommManager.prototype.comm_msg = function (msg) {
        var content = msg.content;
        var comm = this.comms[content.comm_id];
        if (comm === undefined) {
            return;
        }
        try {
            comm.handle_msg(msg);
        } catch (e) {
            console.log("Exception handling comm msg: ", e, e.stack, msg);
        }
    };
    
    //-----------------------------------------------------------------------
    // Comm base class
    //-----------------------------------------------------------------------
    
    var Comm = function (target_name, comm_id) {
        this.target_name = target_name;
        this.comm_id = comm_id || IPython.utils.uuid();
        this._msg_callback = this._close_callback = null;
    };
    
    // methods for sending messages
    Comm.prototype.open = function (data, callbacks, metadata) {
        var content = {
            comm_id : this.comm_id,
            target_name : this.target_name,
            data : data || {},
        };
        return this.kernel.send_shell_message("comm_open", content, callbacks, metadata);
    };
    
    Comm.prototype.send = function (data, callbacks, metadata) {
        var content = {
            comm_id : this.comm_id,
            data : data || {},
        };
        return this.kernel.send_shell_message("comm_msg", content, callbacks, metadata);
    };
    
    Comm.prototype.close = function (data, callbacks, metadata) {
        var content = {
            comm_id : this.comm_id,
            data : data || {},
        };
        return this.kernel.send_shell_message("comm_close", content, callbacks, metadata);
    };
    
    // methods for registering callbacks for incoming messages
    Comm.prototype._register_callback = function (key, callback) {
        this['_' + key + '_callback'] = callback;
    };
    
    Comm.prototype.on_msg = function (callback) {
        this._register_callback('msg', callback);
    };
    
    Comm.prototype.on_close = function (callback) {
        this._register_callback('close', callback);
    };
    
    // methods for handling incoming messages
    
    Comm.prototype._maybe_callback = function (key, msg) {
        var callback = this['_' + key + '_callback'];
        if (callback) {
            try {
                callback(msg);
            } catch (e) {
                console.log("Exception in Comm callback", e, e.stack, msg);
            }
        }
    };
    
    Comm.prototype.handle_msg = function (msg) {
        this._maybe_callback('msg', msg);
    };
    
    Comm.prototype.handle_close = function (msg) {
        this._maybe_callback('close', msg);
    };
    
    IPython.CommManager = CommManager;
    IPython.Comm = Comm;
    
    return IPython;

}(IPython));

