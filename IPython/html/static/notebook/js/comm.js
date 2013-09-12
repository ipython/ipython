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
        this.targets = {comm : Comm};
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
    
    CommManager.prototype.register_target = function (target, constructor) {
        // Register a constructor for a given target key
        this.targets[target] = constructor;
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
        var callback = this.targets[content.target];
        if (callback === undefined) {
            console.log("No such target registered: ", content.target);
            console.log("Available targets are: ", this.targets);
            return;
        }
        var comm = new Comm(content.comm_id);
        this.register_comm(comm);
        callback(comm);
        comm.handle_open(content.data);
    };
    
    CommManager.prototype.comm_close = function (msg) {
        var content = msg.content;
        var comm = this.comms[content.comm_id];
        if (comm === undefined) {
            return;
        }
        delete this.comms[content.comm_id];
        comm.handle_close(content.data);
    };
    
    CommManager.prototype.comm_msg = function (msg) {
        var content = msg.content;
        var comm = this.comms[content.comm_id];
        if (comm === undefined) {
            return;
        }
        comm.handle_msg(content.data);
    };
    
    //-----------------------------------------------------------------------
    // Comm base class
    //-----------------------------------------------------------------------
    
    var Comm = function (comm_id) {
        this.comm_id = comm_id;
        this.target = 'comm';
    };
    
    // methods for sending messages
    Comm.prototype.open = function (data) {
        var content = {
            comm_id : this.comm_id,
            target : this.target,
            data : data || {},
        };
        this.kernel.send_shell_message("comm_open", content);
    };
    
    Comm.prototype.send = function (data) {
        var content = {
            comm_id : this.comm_id,
            data : data || {},
        };
        return this.kernel.send_shell_message("comm_msg", content);
    };
    
    Comm.prototype.close = function (data) {
        var content = {
            comm_id : this.comm_id,
            data : data || {},
        };
        return this.kernel.send_shell_message("comm_close", content);
    };
    
    // methods for handling incoming messages
    
    Comm.prototype.handle_open = function (data) {
        $([this]).trigger("comm_open", data);
    };
    
    Comm.prototype.handle_msg = function (data) {
        $([this]).trigger("comm_msg", data);
    };
    
    Comm.prototype.handle_close = function (data) {
        $([this]).trigger("comm_close", data);
    };
    
    IPython.CommManager = CommManager;
    IPython.Comm = Comm;

    return IPython;

}(IPython));

