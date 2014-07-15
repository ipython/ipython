// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    "widgets/js/init",
    "base/js/frame"
], function(widgetmanager, frame) { 
    var communicator = new frame.FrameCommunicator(parent);
    var widget_manager = null;

    communicator.on_msg(function (msg, respond) {
        widget_manager = new widgetmanager.WidgetManager(
            msg.comm_manager, 
            msg.get_msg_cell);
    });
});
