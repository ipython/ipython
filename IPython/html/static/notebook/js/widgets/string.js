require(["../static/notebook/js/widget"], function(){
    var StringWidgetModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('StringWidgetModel', StringWidgetModel);

    var LabelView = IPython.WidgetView.extend({
      
        // Called when view is rendered.
        render : function(){
            this.$el = $('<div />');
            this.update(); // Set defaults.
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            this.$el.html(this.model.get('value'));
            return IPython.WidgetView.prototype.update.call(this);
        },
        
    });

    IPython.notebook.widget_manager.register_widget_view('LabelView', LabelView);

    var TextareaView = IPython.WidgetView.extend({
      
        // Called when view is rendered.
        render : function(){
            this.$el
                .html('');
            this.$textbox = $('<textarea />')
                .attr('rows', 5)
                .appendTo(this.$el);
            this.update(); // Set defaults.
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            if (!this.user_invoked_update) {
                this.$textbox.val(this.model.get('value'));
            }
            return IPython.WidgetView.prototype.update.call(this);
        },
        
        events: {"keyup textarea" : "handleChanging",
                "paste textarea" : "handleChanging",
                "cut textarea" : "handleChanging"},
        
        // Handles and validates user input.
        handleChanging: function(e) { 
            this.user_invoked_update = true;
            this.model.set('value', e.target.value);
            this.model.update_other_views(this);
            this.user_invoked_update = false;
        },
    });

    IPython.notebook.widget_manager.register_widget_view('TextareaView', TextareaView);

    var TextboxView = IPython.WidgetView.extend({
      
        // Called when view is rendered.
        render : function(){
            this.$el
                .html('');
            this.$textbox = $('<input type="text" />')
                .addClass('input')
                .appendTo(this.$el);
            this.update(); // Set defaults.
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            if (!this.user_invoked_update) {
                this.$textbox.val(this.model.get('value'));
            }
            return IPython.WidgetView.prototype.update.call(this);
        },
        
        events: {"keyup input" : "handleChanging",
                "paste input" : "handleChanging",
                "cut input" : "handleChanging"},
        
        // Handles and validates user input.
        handleChanging: function(e) { 
            this.user_invoked_update = true;
            this.model.set('value', e.target.value);
            this.model.update_other_views(this);
            this.user_invoked_update = false;
        },
    });

    IPython.notebook.widget_manager.register_widget_view('TextboxView', TextboxView);
});
