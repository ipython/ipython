// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    "widgets/js/init",
    "base/js/frame"
], function(widgetmanager, frame) { 
    var communicator = new frame.FrameCommunicator(parent);
    var widget_manager = null;

    var CellProxy = function (){

    };

    var get_msg_cell = function (msg_id) {
        return CellProxy();
    };

    var get_widget_msg_cell = function (msg_id) {

    };

    var register_target = function () {

    };

    communicator.on_msg(function (msg, respond) {
        widget_manager = new widgetmanager.WidgetManager({
            'get_widget_msg_cell': get_widget_msg_cell,
            'get_msg_cell': get_msg_cell,
            'register_target': register_target
        });
    });
});
