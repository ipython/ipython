// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    "widgets/js/init",
    "base/js/frame",
    "base/js/utils"
], function(widgetmanager, frame, utils) { 
    /* Messages
       --------
       > comm_send(comm_id, msg, iopub_status_callback_id, cell_id)
       > register_target(model_name, callback_id)
       > get_msg_cell(msg_id) as cell_id

       < init()
       < comm_on_close(comm_id, msg)
       < comm_on_msg(comm_id, msg) 
       < comm_opened(callback_id, comm_id, msg)
       < iopub_status(callback_id, msg) 
       < new_widget_area(cell_id, frame_name)
       < del_widget_area(cell_id)
    */

    var communicator = new frame.FrameCommunicator(parent);
    var widget_manager = null;

    var comms = {};
    var iopub_status_callbacks = {};
    var CommProxy = function (id){
        this.id = id;
        this.close_callback = null;
        this.msg_callback = null;
        comms[id] = this;
    };

    CommProxy.prototype.on_close = function (callback) {
        this.close_callback = callback;
    };
    
    CommProxy.prototype.on_msg = function (callback) {
        this.msg_callback = callback;
    };
    
    CommProxy.prototype.send = function (msg, callbacks) {
        var status_callback_id = null;
        if (callbacks && callbacks.iopub && callbacks.iopub.status) {
            status_callback_id = utils.uuid();
            iopub_status_callbacks[status_callback_id] = callbacks.iopub.status;
        }

        var cell = null;
        if (callbacks && callbacks.view) {
            cell = callbacks.view.options.cell;
        }
        communicator.send(this.id, msg, status_callback_id, cell);
    };


    var show_widgetarea = function (cell) {
        parent[cell_frames[cell]].widget_area.show();
    };

    var get_msg_cell = function (msg_id, callback) {
        communicator.send({'msg_id': msg_id}, function (msg, respond) {
            callback(msg.cell_id);
        });
    };

    var display_view = function (cell, view) {
        parent[cell_frames[cell]].widget_area.display_view(view);
    };

    var comm_callbacks = {};
    var register_target = function (model_name, callback) {
        var id = utils.uuid();
        comm_callbacks[id] = callback;
        communicator.send({'model_name': model_name, 'callback_id': id});
    };

    var cell_frames = {};
    communicator.on_msg(function (msg, respond) {
        var comm;
        var callback;
        switch (msg.type) {
            case 'init':
                widget_manager = new widgetmanager.WidgetManager({
                    'get_widget_msg_cell': get_widget_msg_cell,
                    'get_msg_cell': get_msg_cell,
                    'register_target': register_target,
                    'display_view': display_view
                });    
                break;

            case 'comm_on_close':
                // msg.comm_id, msg.msg
                if (comms[msg.comm_id]) {
                    comm = comms[msg.comm_id];
                    if (comm.close_callback) {
                        comm.close_callback(msg.msg);
                    }
                }
                break;

            case 'comm_on_msg':
                // msg.comm_id, msg.msg
                if (comms[msg.comm_id]) {
                    comm = comms[msg.comm_id];
                    if (comm.msg_callback) {
                        comm.msg_callback(msg.msg);
                    }
                }
                break;

            case 'comm_opened':
                // msg.callback_id, msg.comm_id, msg.msg
                comm = CommProxy(msg.comm_id);
                callback = comm_callbacks[msg.callback_id];
                if (callback) {
                    callback(comm, msg.msg);
                }
                break;

            case 'iopub_status':
                // msg.callback_id, msg.msg
                callback = iopub_status_callbacks[msg.callback_id];
                if (callback) {
                    callback(msg.msg);
                }
                break;

            case 'new_widget_area':
                // msg.cell_id, msg.frame_name
                cell_frames[msg.cell_id] = msg.frame_name;
                break;

            case 'del_widget_area':
                // msg.cell_id
                delete cell_frames[msg.cell_id];
                break;
        }
    });
});
