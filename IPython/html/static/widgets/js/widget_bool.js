// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/widget",
    "jquery",
    "bootstrap",
], function(widget, $){

    var CheckboxView = widget.DOMWidgetView.extend({
        render : function(){
            /**
             * Called when view is rendered.
             */
            this.$el
                .addClass('widget-hbox widget-checkbox');
            this.$label = $('<div />')
                .addClass('widget-label')
                .appendTo(this.$el)
                .hide();
            this.$checkbox = $('<input />')
                .attr('type', 'checkbox')
                .appendTo(this.$el)
                .click($.proxy(this.handle_click, this));

            this.update(); // Set defaults.
        },

        update_attr: function(name, value) {
            /**
             * Set a css attr of the widget view.
             */
            if (name == 'padding' || name == 'margin') {
                this.$el.css(name, value);
            } else {
                this.$checkbox.css(name, value);
            }
        },

        handle_click: function() {
            /**
             * Handles when the checkbox is clicked.
             *
             * Calling model.set will trigger all of the other views of the 
             * model to update.
             */
            var value = this.model.get('value');
            this.model.set('value', ! value, {updated_view: this});
            this.touch();
        },
        
        update : function(options){
            /**
             * Update the contents of this view
             *
             * Called when the model is changed.  The model may have been 
             * changed by another view or by a state update from the back-end.
             */
            this.$checkbox.prop('checked', this.model.get('value'));

            if (options === undefined || options.updated_view != this) {
                var disabled = this.model.get('disabled');
                this.$checkbox.prop('disabled', disabled);

                var description = this.model.get('description');
                if (description.trim().length === 0) {
                    this.$label.hide();
                } else {
                    this.typeset(this.$label, description);
                    this.$label.show();
                }
            }
            return CheckboxView.__super__.update.apply(this);
        },
        
    });


    var ToggleButtonView = widget.DOMWidgetView.extend({
        render : function() {
            /**
             * Called when view is rendered.
             */
            var that = this;
            this.setElement($('<button />')
                .addClass('btn btn-default')
                .attr('type', 'button')
                .on('click', function (e) {
                    e.preventDefault();
                    that.handle_click();
                }));
            this.$el.attr("data-toggle", "tooltip");
            this.model.on('change:button_style', function(model, value) {
                this.update_button_style();
            }, this);
            this.update_button_style('');

            this.update(); // Set defaults.
        },

        update_button_style: function(previous_trait_value) {
            var class_map = {
                primary: ['btn-primary'],
                success: ['btn-success'],
                info: ['btn-info'],
                warning: ['btn-warning'],
                danger: ['btn-danger']
            };
            this.update_mapped_classes(class_map, 'button_style', previous_trait_value);
        },
        
        update : function(options){
            /**
             * Update the contents of this view
             *
             * Called when the model is changed.  The model may have been 
             * changed by another view or by a state update from the back-end.
             */
            if (this.model.get('value')) {
                this.$el.addClass('active');
            } else {
                this.$el.removeClass('active');
            }

            if (options === undefined || options.updated_view != this) {

                var disabled = this.model.get('disabled');
                this.$el.prop('disabled', disabled);

                var description = this.model.get('description');
                this.$el.attr("title", this.model.get("tooltip"));
                if (description.trim().length === 0) {
                    this.$el.html("&nbsp;"); // Preserve button height
                } else {
                    this.$el.text(description);
                }
            }
            return ToggleButtonView.__super__.update.apply(this);
        },
        
        handle_click: function(e) { 
            /**
             * Handles and validates user input.
             *
             * Calling model.set will trigger all of the other views of the 
             * model to update.
             */
            var value = this.model.get('value');
            this.model.set('value', ! value, {updated_view: this});
            this.touch();
        },
    });

    return {
        'CheckboxView': CheckboxView,
        'ToggleButtonView': ToggleButtonView,
    };
});
