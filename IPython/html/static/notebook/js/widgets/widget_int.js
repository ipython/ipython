//----------------------------------------------------------------------------
//  Copyright (C) 2013 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// IntWidget
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 **/

define(["notebook/js/widgets/widget"], function(WidgetManager){

    var IntSliderView = IPython.DOMWidgetView.extend({    
        render : function(){
            // Called when view is rendered.
            this.$el
                .addClass('widget-hbox-single');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-hlabel')
                .hide();
            this.$slider = $('<div />')
                .slider({})
                .addClass('slider');
            
            // Put the slider in a container 
            this.$slider_container = $('<div />')
                .addClass('widget-hslider')
                .append(this.$slider);    
            this.$el_to_style = this.$slider_container; // Set default element to style
            this.$el.append(this.$slider_container);
            
            // Set defaults.
            this.update();
        },
        
        update : function(options){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            if (options === undefined || options.updated_view != this) {
                // JQuery slider option keys.  These keys happen to have a
                // one-to-one mapping with the corrosponding keys of the model.
                var jquery_slider_keys = ['step', 'max', 'min', 'disabled'];
                var that = this;
                _.each(jquery_slider_keys, function(key, i) {
                    var model_value = that.model.get(key);
                    if (model_value !== undefined) {
                        that.$slider.slider("option", key, model_value);
                    }
                });

                // WORKAROUND FOR JQUERY SLIDER BUG.
                // The horizontal position of the slider handle
                // depends on the value of the slider at the time
                // of orientation change.  Before applying the new
                // workaround, we set the value to the minimum to
                // make sure that the horizontal placement of the
                // handle in the vertical slider is always 
                // consistent.
                var orientation = this.model.get('orientation');
                var value = this.model.get('min');
                this.$slider.slider('option', 'value', value);
                this.$slider.slider('option', 'orientation', orientation);
                value = this.model.get('value');
                this.$slider.slider('option', 'value', value);

                // Use the right CSS classes for vertical & horizontal sliders
                if (orientation=='vertical') {
                    this.$slider_container
                        .removeClass('widget-hslider')
                        .addClass('widget-vslider');
                    this.$el
                        .removeClass('widget-hbox-single')
                        .addClass('widget-vbox-single');
                    this.$label
                        .removeClass('widget-hlabel')
                        .addClass('widget-vlabel');

                } else {
                    this.$slider_container
                        .removeClass('widget-vslider')
                        .addClass('widget-hslider');
                    this.$el
                        .removeClass('widget-vbox-single')
                        .addClass('widget-hbox-single');
                    this.$label
                        .removeClass('widget-vlabel')
                        .addClass('widget-hlabel');
                }

                var description = this.model.get('description');
                if (description.length === 0) {
                    this.$label.hide();
                } else {
                    this.$label.text(description);
                    this.$label.show();
                }
            }
            return IntSliderView.__super__.update.apply(this);
        },
        
        events: {
            // Dictionary of events and their handlers.
            "slide" : "handleSliderChange"
        }, 

        handleSliderChange: function(e, ui) { 
            // Called when the slider value is changed.

            // Calling model.set will trigger all of the other views of the 
            // model to update.
            this.model.set('value', ~~ui.value, {updated_view: this}); // Double bit-wise not to truncate decimel
            this.touch();
        },
    });
    WidgetManager.register_widget_view('IntSliderView', IntSliderView);


    var IntTextView = IPython.DOMWidgetView.extend({    
        render : function(){
            // Called when view is rendered.
            this.$el
                .addClass('widget-hbox-single');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-hlabel')
                .hide();
            this.$textbox = $('<input type="text" />')
                .addClass('input')
                .addClass('widget-numeric-text')
                .appendTo(this.$el);
            this.$el_to_style = this.$textbox; // Set default element to style
            this.update(); // Set defaults.
        },
        
        update : function(options){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            if (options === undefined || options.updated_view != this) {
                var value = this.model.get('value');
                if (parseInt(this.$textbox.val()) != value) {
                    this.$textbox.val(value);
                }
                
                if (this.model.get('disabled')) {
                    this.$textbox.attr('disabled','disabled');
                } else {
                    this.$textbox.removeAttr('disabled');
                }

                var description = this.model.get('description');
                if (description.length === 0) {
                    this.$label.hide();
                } else {
                    this.$label.text(description);
                    this.$label.show();
                }
            }
            return IntTextView.__super__.update.apply(this);
        },

        events: {
            // Dictionary of events and their handlers.
            "keyup input"  : "handleChanging",
            "paste input"  : "handleChanging",
            "cut input"    : "handleChanging",

            // Fires only when control is validated or looses focus.
            "change input" : "handleChanged"
        }, 
        
        handleChanging: function(e) { 
            // Handles and validates user input.
            
            // Try to parse value as a float.
            var numericalValue = 0;
            if (e.target.value !== '') {
                numericalValue = parseInt(e.target.value);
            }
            
            // If parse failed, reset value to value stored in model.
            if (isNaN(numericalValue)) {
                e.target.value = this.model.get('value');
            } else if (!isNaN(numericalValue)) {
                if (this.model.get('max') !== undefined) {
                    numericalValue = Math.min(this.model.get('max'), numericalValue);
                }
                if (this.model.get('min') !== undefined) {
                    numericalValue = Math.max(this.model.get('min'), numericalValue);
                }
                
                // Apply the value if it has changed.
                if (numericalValue != this.model.get('value')) {
            
                    // Calling model.set will trigger all of the other views of the 
                    // model to update.
                    this.model.set('value', numericalValue, {updated_view: this});
                    this.touch();
                }
            }
        },
        
        handleChanged: function(e) { 
            // Applies validated input.
            if (this.model.get('value') != e.target.value) {
                e.target.value = this.model.get('value');
            }
        }
    });
    WidgetManager.register_widget_view('IntTextView', IntTextView);
});
