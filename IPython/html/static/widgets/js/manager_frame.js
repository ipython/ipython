// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "jquery",
    "base/js/frame",
    "base/js/utils"
], function($, frame, utils){
    /* Messages
       --------
       < *comm_send(comm_id, msg, iopub_status_callback_id, cell_id)
       < *register_target(model_name, callback_id)
       < *get_msg_cell(msg_id) as cell_id

       > *init()
       > *comm_opened(callback_id, comm_id, msg)
       > *new_widget_area(cell_id, frame_name)
       > *del_widget_area(cell_id)
       > *iopub_status(callback_id, msg) 
       > comm_on_close(comm_id, msg)
       > comm_on_msg(comm_id, msg) 
    */
    var WidgetManagerFrame = function(comm_manager, notebook, events) {
        this.comm_manager = comm_manager;
        this.notebook = notebook;
        this.events = events;

        this.$el = $('<iframe />')
            .attr('src', '/widgetmanager')
            .attr('name', 'widgetmanager');
        this.communicator = new frame.FrameCommunicator(this.$el, true);
        var that = this;
        this.communicator.on_msg(function (msg, respond) {
            switch (msg.type) {
                case 'comm_send':
                    that._handle_comm_send(msg.comm_id, msg.msg, msg.iopub_status_callback_id, msg.cell_id);
                    break;
                case 'register_target':
                    that._handle_register_target(msg.model_name, msg.callback_id);
                    break;
                case 'get_msg_cell':
                    var cell = that._get_msg_cell(msg.msg_id);
                    var cell_id = null;
                    if (cell) { cell_id = cell.cell_id; }
                    respond({'cell_id': cell_id});
                    break;
            }
        });

        events.on('create.Cell', function(event, data) {
            that.register_cell(data.cell.cell_id);
        });
        events.on('delete.Cell', function(event, data) {
            var id = data.cell.cell_id;
            that.communicator.send({
                type: 'del_widget_area',
                cell_id: id, 
            });
        });
    };

    WidgetManagerFrame.prototype.init = function() {
        this.communicator.send({
            'type': 'init',
        });
    };

    WidgetManagerFrame.prototype.register_cell = function(cell_id) {
        this.communicator.send({
            type: 'new_widget_area',
            'cell_id': cell_id, 
            frame_name: 'widgetarea_' + cell_id
        });
    };

    WidgetManagerFrame.prototype._handle_comm_send = function(comm_id, msg, iopub_status_callback_id, cell_id) {
        var comm = that.comm_manager.comms[comm_id];
        if (comm) {
            var callbacks = that._make_callbacks(cell_id, iopub_status_callback_id);
            comm.send(msg, callbacks);
        }
    };

    WidgetManagerFrame.prototype._handle_register_target = function(model_name, callback_id) {
        var that = this;
        this.comm_manager.register_target(model_name, function(comm, comm_msg) {
            comm.on_close(function(msg) {
                that.communicator.send({
                    type: 'comm_on_close',
                    comm_id: comm.comm_id,
                    'msg': msg
                });
            });
            
            comm.on_msg(function(msg) {
                that.communicator.send({
                    type: 'comm_on_msg',
                    comm_id: comm.comm_id,
                    'msg': msg
                });
            });

            that.communicator.send({
                type: 'comm_opened',
                'callback_id': callback_id,
                comm_id: comm.comm_id,
                'msg': comm_msg
            });
        });
    };

    WidgetManagerFrame.prototype._get_msg_cell = function(msg_id) {
        var cell = null;
        // First, check to see if the msg was triggered by cell execution.
        if (this.notebook) {
            cell = this.notebook.get_msg_cell(msg_id);
        }
        if (cell !== null) {
            return cell;
        }
        // Second, check to see if a get_cell callback was defined
        // for the message.  get_cell callbacks are registered for
        // widget messages, so this block is actually checking to see if the
        // message was triggered by a widget.
        var kernel = this.comm_manager.kernel;
        if (kernel) {
            var callbacks = kernel.get_callbacks_for_msg(msg_id);
            if (callbacks && callbacks.iopub &&
                callbacks.iopub.get_cell !== undefined) {
                return callbacks.iopub.get_cell();
            }
        }
        
        // Not triggered by a cell or widget (no get_cell callback 
        // exists).
        return null;
    };

    WidgetManagerFrame.prototype._make_callbacks = function(cell_id, iopub_status_callback_id) {
        // Callback handlers specific a cell

        // Try to make output handlers
        var callbacks = {};
        var cell = this._get_cell(cell_id);
        var handle_output = null;
        var handle_clear_output = null;
        if (cell.output_area) {
            handle_output = $.proxy(cell.output_area.handle_output, cell.output_area);
            handle_clear_output = $.proxy(cell.output_area.handle_clear_output, cell.output_area);
        }

        // Create callback dict using what is known
        var that = this;
        callbacks = {
            iopub : {
                output : handle_output,
                clear_output : handle_clear_output,

                // Special function only registered by widget messages.
                // Allows us to get the cell for a message so we know
                // where to add widgets if the code requires it.
                get_cell: function() {
                    return cell;
                },

                status: function(msg) {
                    that.communicator.send({
                        'type': 'iopub_status',
                        'callback_id': iopub_status_callback_id, 
                        'msg': msg 
                    });
                },
            },
        };
        return callbacks;
    };

    WidgetManagerFrame.prototype._get_cell = function(cell_id) {
        if (this.notebook) {
            var cells = this.notebook.get_cells();
            for (var i = 0; i < cells.length; i++) {
                var cell = cells[i];
                if (cell.cell_id == cell_id) {
                    return cell;
                }
            }
        }
        return null;
    }

    return {'WidgetManagerFrame': WidgetManagerFrame};
});
