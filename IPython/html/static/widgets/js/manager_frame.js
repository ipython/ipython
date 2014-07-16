// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "jquery",
    "base/js/frame"
], function($, frame){
    /* Messages
       --------
       < comm_send(comm_id, msg, iopub_status_callback_id, cell_id)
       < register_target(model_name, callback_id)
       < get_msg_cell(msg_id) as cell_id

       > init()
       > comm_on_close(comm_id, msg)
       > comm_on_msg(comm_id, msg) 
       > comm_opened(callback_id, comm_id, msg)
       > iopub_status(callback_id, msg) 
       > new_widget_area(cell_id, frame_name)
    */
    var WidgetManagerFrame = function(container) {
        this.$el = $('<iframe />')
            .attr('src', '/widgetmanager')
            .attr('name', 'widgetmanager');
        this.communicator = new frame.FrameCommunicator(this.$el, true);
        this.communicator.on_msg(function (msg, respond) {

        });
    };

    WidgetManagerFrame.prototype.init = function() {
        this.communicator.msg({
            'type': 'init',
        });
    };





    WidgetManagerFrame.prototype.callbacks = function (view) {
        // callback handlers specific a view
        var callbacks = {};
        if (view && view.options.cell) {

            // Try to get output handlers
            var cell = view.options.cell;
            var handle_output = null;
            var handle_clear_output = null;
            
            // TODO: WIRE UP CALLBACKS SOME HOW!!
            // if (cell.output_area) {
            //     handle_output = $.proxy(cell.output_area.handle_output, cell.output_area);
            //     handle_clear_output = $.proxy(cell.output_area.handle_clear_output, cell.output_area);
            // }

            // Create callback dict using what is known
            var that = this;
            callbacks = {
                iopub : {
                    output : handle_output,
                    clear_output : handle_clear_output,

                    // Special function only registered by widget messages.
                    // Allows us to get the cell for a message so we know
                    // where to add widgets if the code requires it.
                    get_cell : function () {
                        return cell;
                    },
                },
            };
        }
        return callbacks;
    };

    return {'WidgetManagerFrame': WidgetManagerFrame};
});
