// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/widget",
    "jquery",
    'notebook/js/outputarea',
], function(widget, $, outputarea) {
    'use strict';

    var OutputView = widget.DOMWidgetView.extend({
        /**
         * Public constructor
         */
        initialize: function (parameters) {
            OutputView.__super__.initialize.apply(this, [parameters]);
            this.model.on('msg:custom', this._handle_route_msg, this);
        },

        /**
         * Called when view is rendered.
         */
        render: function(){
            this.output_area = new outputarea.OutputArea({
                selector: this.$el, 
                prompt_area: false, 
                events: this.model.widget_manager.notebook.events, 
                keyboard_manager: this.model.widget_manager.keyboard_manager });

            // Make output area reactive.
            var that = this;
            this.output_area.element.on('changed', function() {
                that.model.set('contents', that.output_area.element.html());
            });
            this.model.on('change:contents', function(){
                var html = this.model.get('contents');
                if (this.output_area.element.html() != html) {
                    this.output_area.element.html(html);
                }
            }, this);

            // Set initial contents.
            this.output_area.element.html(this.model.get('contents'));
        },
        
        /**
         * Handles re-routed iopub messages.
         */
        _handle_route_msg: function(msg) {
            if (msg) {
                var msg_type = msg.msg_type;
                if (msg_type=='clear_output') {
                    this.output_area.handle_clear_output(msg);
                } else {
                    this.output_area.handle_output(msg);
                }
            }
        },
    });

    return {
        'OutputView': OutputView,
    };
});
