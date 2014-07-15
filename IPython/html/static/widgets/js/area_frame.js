// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "jquery",
    "base/js/utils",
    "base/js/frame"
], function($, utils, frame){

    var WidgetAreaFrame = function() {
        var guid = utils.uuid();
        this.name = 'widgetarea_' + guid;
        this.$el = $('<iframe />')
            .attr('src', '/widgetarea')
            .attr('name', this.name);
        this.communicator = new frame.FrameCommunicator(this.$el, true);
    };

    WidgetAreaFrame.prototype.clear = function() {
        this.communicator.msg({type: 'clear'});
    };

    return {
        'WidgetAreaFrame': WidgetAreaFrame,
    };
});
