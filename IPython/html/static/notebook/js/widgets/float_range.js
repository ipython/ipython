require(["notebook/js/widget"], function(){
    var FloatRangeWidgetModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('FloatRangeWidgetModel', FloatRangeWidgetModel);

    var FloatSliderView = IPython.WidgetView.extend({
        
        // Called when view is rendered.
        render : function(){
            this.$el
                .addClass('widget-hbox-single')
                .html('');
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
            this.$el.append(this.$slider_container);
            
            // Set defaults.
            this.update();
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            // Slider related keys.
            var _keys = ['step', 'max', 'min', 'disabled'];
            for (var index in _keys) {
                var key = _keys[index];
                if (this.model.get(key) != undefined) {
                    this.$slider.slider("option", key, this.model.get(key));
                }
            }

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
            var value = this.model.get('value');
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
            if (description.length == 0) {
                this.$label.hide();
            } else {
                this.$label.html(description);
                this.$label.show();
            }
            return IPython.WidgetView.prototype.update.call(this);
        },
        
        // Handles: User input
        events: { "slide" : "handleSliderChange" }, 
        handleSliderChange: function(e, ui) { 
            this.model.set('value', ui.value); 
            this.model.update_other_views(this);
        },
    });

    IPython.notebook.widget_manager.register_widget_view('FloatSliderView', FloatSliderView);


    var FloatTextView = IPython.WidgetView.extend({
        
        // Called when view is rendered.
        render : function(){
            this.$el
                .addClass('widget-hbox-single')
                .html('');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-hlabel')
                .hide();
            this.$textbox = $('<input type="text" />')
                .addClass('input')
                .addClass('widget-numeric-text')
                .appendTo(this.$el);
            this.update(); // Set defaults.
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            var value = this.model.get('value');
            if (!this.changing && parseFloat(this.$textbox.val()) != value) {
                this.$textbox.val(value);
            }
            
            if (this.model.get('disabled')) {
                this.$textbox.attr('disabled','disabled');
            } else {
                this.$textbox.removeAttr('disabled');
            }

            var description = this.model.get('description');
            if (description.length == 0) {
                this.$label.hide();
            } else {
                this.$label.html(description);
                this.$label.show();
            }
            return IPython.WidgetView.prototype.update.call(this);
        },
        
        
        events: {"keyup input" : "handleChanging",
                "paste input" : "handleChanging",
                "cut input" : "handleChanging",
                "change input" : "handleChanged"}, // Fires only when control is validated or looses focus.
        
        // Handles and validates user input.
        handleChanging: function(e) { 
            
            // Try to parse value as a float.
            var numericalValue = 0.0;
            if (e.target.value != '') {
                numericalValue = parseFloat(e.target.value);
            }
            
            // If parse failed, reset value to value stored in model.
            if (isNaN(numericalValue)) {
                e.target.value = this.model.get('value');
            } else if (!isNaN(numericalValue)) {
                if (this.model.get('max') != undefined) {
                    numericalValue = Math.min(this.model.get('max'), numericalValue);
                }
                if (this.model.get('min') != undefined) {
                    numericalValue = Math.max(this.model.get('min'), numericalValue);
                }

                // Apply the value if it has changed.
                if (numericalValue != this.model.get('value')) {
                    this.changing = true;
                    this.model.set('value', numericalValue);
                    this.model.update_other_views(this);
                    this.changing = false;
                }
            }
        },
        
        // Applies validated input.
        handleChanged: function(e) { 
            // Update the textbox
            if (this.model.get('value') != e.target.value) {
                e.target.value = this.model.get('value');
            }
        }
    });

    IPython.notebook.widget_manager.register_widget_view('FloatTextView', FloatTextView);


    var ProgressView = IPython.WidgetView.extend({
        
        // Called when view is rendered.
        render : function(){
            this.$el
                .addClass('widget-hbox-single')
                .html('');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-hlabel')
                .hide();
            this.$progress = $('<div />')
                .addClass('progress')
                .addClass('widget-progress')
                .appendTo(this.$el);
            this.$bar = $('<div />')
                .addClass('bar')
                .css('width', '50%')
                .appendTo(this.$progress);
            this.update(); // Set defaults.
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            var value = this.model.get('value');
            var max = this.model.get('max');
            var min = this.model.get('min');
            var percent = 100.0 * (value - min) / (max - min);
            this.$bar.css('width', percent + '%');
            
            var description = this.model.get('description');
            if (description.length == 0) {
                this.$label.hide();
            } else {
                this.$label.html(description);
                this.$label.show();
            }
            return IPython.WidgetView.prototype.update.call(this);
        },
        
    });

    IPython.notebook.widget_manager.register_widget_view('ProgressView', ProgressView);
});
