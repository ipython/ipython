// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "jquery",
    "base/js/utils",
    "base/js/frame"
], function($, utils, frame){

    var WidgetAreaFrame = function(guid) {
        this.name = 'widgetarea_' + guid;
        this.$el = $('<iframe />')
            .attr('src', '/widgetarea')
            .attr('name', this.name)
            .css('width', '100%')
            .css('height', 0);
        this.communicator = new frame.FrameCommunicator(this.$el, true);
        var that = this;
        this.communicator.on_msg(function(msg, respond) {
            if (msg.type == 'resize') {
                that.$el.height(msg.height);
            }
        });
    };

    WidgetAreaFrame.prototype.clear = function() {
        this.communicator.send({type: 'clear'});
    };

    return {
        'WidgetAreaFrame': WidgetAreaFrame,
    };
});
