
require(["../static/notebook/js/widget"], function(){
    
    var BoolWidgetModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('BoolWidgetModel', BoolWidgetModel);

    var CheckboxView = IPython.WidgetView.extend({
      
        // Called when view is rendered.
        render : function(){
            this.$el
                .html('');

            var $label = $('<label />')
                .addClass('checkbox')
                .appendTo(this.$el);
            this.$checkbox = $('<input />')
                .attr('type', 'checkbox')
                .appendTo($label);
            this.$checkbox_label = $('<div />')
                .appendTo($label);

            this.update(); // Set defaults.
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            if (!this.user_invoked_update) {
                this.$checkbox.prop('checked', this.model.get('value'));
                this.$checkbox_label.html(this.model.get('description'));
            }
            return IPython.WidgetView.prototype.update.call(this);
        },
        
        events: {"change input" : "handleChanged"},
        
        // Handles and validates user input.
        handleChanged: function(e) { 
            this.user_invoked_update = true;
            this.model.set('value', $(e.target).prop('checked'));
            this.model.update_other_views(this);
            this.user_invoked_update = false;
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
                this.$button.html(this.model.get('description'));
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
