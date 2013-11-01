
require(["notebook/js/widget"], function(){
    
    var BoolWidgetModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('BoolWidgetModel', BoolWidgetModel);

    var CheckboxView = IPython.WidgetView.extend({
      
        // Called when view is rendered.
        render : function(){
            this.$el = $('<div />')
                .addClass('widget-hbox-single');
            this.$label = $('<div />')
                .addClass('widget-hlabel')
                .appendTo(this.$el)
                .hide();
            var that = this;
            this.$checkbox = $('<input />')
                .attr('type', 'checkbox')
                .click(function(el) {
                    that.user_invoked_update = true;
                    that.model.set('value', that.$checkbox.prop('checked'));
                    that.model.update_other_views(that);
                    that.user_invoked_update = false;
                })
                .appendTo(this.$el);

            this.$el_to_style = this.$checkbox; // Set default element to style
            this.update(); // Set defaults.
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            if (!this.user_invoked_update) {
                this.$checkbox.prop('checked', this.model.get('value'));

                var disabled = this.model.get('disabled');
                this.$checkbox.prop('disabled', disabled);

                var description = this.model.get('description');
                if (description.length == 0) {
                    this.$label.hide();
                } else {
                    this.$label.html(description);
                    this.$label.show();
                }
            }
            return IPython.WidgetView.prototype.update.call(this);
        },
        
    });

    IPython.notebook.widget_manager.register_widget_view('CheckboxView', CheckboxView);

    var ToggleButtonView = IPython.WidgetView.extend({
      
        // Called when view is rendered.
        render : function(){
            this.$el
                .html('');

            this.$button = $('<button />')
                .addClass('btn')
                .attr('type', 'button')
                .attr('data-toggle', 'button')
                .appendTo(this.$el);
            this.$el_to_style = this.$button; // Set default element to style

            this.update(); // Set defaults.
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            if (!this.user_invoked_update) {
                if (this.model.get('value')) {
                    this.$button.addClass('active');
                } else {
                    this.$button.removeClass('active');
                }

                var disabled = this.model.get('disabled');
                this.$button.prop('disabled', disabled);

                var description = this.model.get('description');
                if (description.length == 0) {
                    this.$button.html(' '); // Preserve button height
                } else {
                    this.$button.html(description);
                }
            }
            return IPython.WidgetView.prototype.update.call(this);
        },
        
        events: {"click button" : "handleClick"},
        
        // Handles and validates user input.
        handleClick: function(e) { 
            this.user_invoked_update = true;
            this.model.set('value', ! $(e.target).hasClass('active'));
            this.model.update_other_views(this);
            this.user_invoked_update = false;
        },
    });

    IPython.notebook.widget_manager.register_widget_view('ToggleButtonView', ToggleButtonView);

});
