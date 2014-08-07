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

define(["widgets/js/widget"], function(WidgetManager){

    var IntRangeSliderView = IPython.DOMWidgetView.extend({
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
                .append(this.$slider)
            this.$el_to_style = this.$slider_container; // Set default element to style
            this.$el.append(this.$slider_container);
            
            this.$readout = $('<div/>')
                .appendTo(this.$el)
                .addClass('widget-hreadout')
                .hide();
            
            // Set defaults.
            this.update();
        },
        
        update : function(options){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            if (options === undefined || options.updated_view != this) {
                // JQuery slider option keys.
                this.$slider.slider("option", "range", true);
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
                // workaround, we set the values  minimum/maximum respectively to
                // make sure that the horizontal placement of the
                // handle in the vertical slider is always 
                // consistent.
                var orientation = this.model.get('orientation');
                var min = this.model.get('min');
                var max = this.model.get('max');
                this.$slider.slider('option', 'values', [min, max]);
                this.$slider.slider('option', 'orientation', orientation);
                var lower_value = this.model.get('lower_value');
                var upper_value = this.model.get('upper_value');
                this.$slider.slider('option', 'values', [lower_value, upper_value]);
                this.$readout.text('(' + lower_value + ', ' + upper_value + ')');

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
                    this.$readout
                        .removeClass('widget-hreadout')
                        .addClass('widget-vreadout');

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
                    this.$readout
                        .removeClass('widget-vreadout')
                        .addClass('widget-hreadout');
                }

                var description = this.model.get('description');
                if (description.length === 0) {
                    this.$label.hide();
                } else {
                    this.$label.text(description);
                    this.$label.show();
                }
                
                var readout = this.model.get('readout');
                if (readout) {
                    this.$readout.show();
                } else {
                    this.$readout.hide();
                }
            }
            return IntRangeSliderView.__super__.update.apply(this);
        },
        
        events: {
            // Dictionary of events and their handlers.
            "slide" : "handleSliderChange"
        }, 

        handleSliderChange: function(e, ui) { 
            // Called when the slider value is changed.

            // Calling model.set will trigger all of the other views of the 
            // model to update.
            var actual_lower_value = this._validate_slide_value(ui.values[0]);
            this.model.set('lower_value', actual_lower_value, {updated_view: this});
            var actual_upper_value = this._validate_slide_value(ui.values[1]);
            this.model.set('upper_value', actual_upper_value, {updated_view: this});
            this.$readout.text('(' + actual_lower_value + ', ' + actual_upper_value + ')');
            this.touch();
        },

        _validate_slide_value: function(x) {
            // Validate the value of the slider before sending it to the back-end
            // and applying it to the other views on the page.

            // Double bit-wise not truncates the decimel (int cast).
            return ~~x;
        },
    });
    WidgetManager.register_widget_view('IntRangeSliderView', IntRangeSliderView);

    // Return the range slider view so it can be inheritted to create the
    // float version.
    return IntRangeSliderView;
});
