// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/widget",
    "jquery",
    'notebook/js/outputarea',
], function(widget, $, outputarea) {
    'use strict';

    var OutputView = widget.DOMWidgetView.extend({
        initialize: function (parameters) {
            /**
             * Public constructor
             */
            OutputView.__super__.initialize.apply(this, [parameters]);
            this.model.on('msg:custom', this._handle_route_msg, this);
        },

        render: function(){
            /**
             * Called when view is rendered.
             */
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
        
        _handle_route_msg: function(content) {
            if (content) {
    //     return {
    //         shell : {
    //             reply : $.proxy(this._handle_execute_reply, this),
    //             payload : {
    //                 set_next_input : $.proxy(this._handle_set_next_input, this),
    //                 page : $.proxy(this._open_with_pager, this)
    //             }
    //         },
    //         iopub : {
    //             output : function() { 
    //                 that.output_area.handle_output.apply(that.output_area, arguments);
    //             }, 
    //             clear_output : function() { 
    //                 that.output_area.handle_clear_output.apply(that.output_area, arguments);
    //             }, 
    //         },
    //         input : $.proxy(this._handle_input_request, this)
    //     };
    // };
                if (content.method == 'push') {
                    cell.push_output_area(this.output_area);
                } else if (content.method == 'pop') {
                    cell.pop_output_area(this.output_area);
                }
            }
        },
    });

    return {
        'OutputView': OutputView,
    };
});
