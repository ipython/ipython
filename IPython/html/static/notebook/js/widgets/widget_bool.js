//----------------------------------------------------------------------------
//  Copyright (C) 2013 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// BoolWidget
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 **/

define(["notebook/js/widgets/widget"], function(widget_manager){
    var CheckboxView = IPython.DOMWidgetView.extend({
      
        // Called when view is rendered.
        render : function(){
            this.$el
                .addClass('widget-hbox-single');
            this.$label = $('<div />')
                .addClass('widget-hlabel')
                .appendTo(this.$el)
                .hide();
            var that = this;
            this.$checkbox = $('<input />')
                .attr('type', 'checkbox')
                .click(function(el) {
            
                    // Calling model.set will trigger all of the other views of the 
                    // model to update.
                    that.model.set('value', that.$checkbox.prop('checked'), {updated_view: this});
                    that.touch();
                })
                .appendTo(this.$el);

            this.$el_to_style = this.$checkbox; // Set default element to style
            this.update(); // Set defaults.
        },
        
        update : function(options){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            if (options === undefined || options.updated_view != this) {
                this.$checkbox.prop('checked', this.model.get('value'));

                var disabled = this.model.get('disabled');
                this.$checkbox.prop('disabled', disabled);

                var description = this.model.get('description');
                if (description.length === 0) {
                    this.$label.hide();
                } else {
                    this.$label.html(description);
                    this.$label.show();
                }
            }
            return CheckboxView.__super__.update.apply(this);
        },
        
    });

    widget_manager.register_widget_view('CheckboxView', CheckboxView);

    var ToggleButtonView = IPython.DOMWidgetView.extend({
      
        // Called when view is rendered.
        render : function(){
            this.setElement($('<button />')
                .addClass('btn')
                .attr('type', 'button')
                .attr('data-toggle', 'button'));

            this.update(); // Set defaults.
        },
        
        update : function(options){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            if (this.model.get('value')) {
                this.$el.addClass('active');
            } else {
                this.$el.removeClass('active');
            }

            if (options === undefined || options.updated_view != this) {
                var disabled = this.model.get('disabled');
                this.$el.prop('disabled', disabled);

                var description = this.model.get('description');
                if (description.length === 0) {
                    this.$el.html(' '); // Preserve button height
                } else {
                    this.$el.html(description);
                }
            }
            return ToggleButtonView.__super__.update.apply(this);
        },
        
        events: {"click" : "handleClick"},
        
        // Handles and validates user input.
        handleClick: function(e) { 

            // Calling model.set will trigger all of the other views of the 
            // model to update.
            this.model.set('value', ! $(this.$el).hasClass('active'), {updated_view: this});
            this.touch();
        },
    });

    widget_manager.register_widget_view('ToggleButtonView', ToggleButtonView);

});
