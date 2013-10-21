
require(["notebook/js/widget"], function(){
    
    var ButtonWidgetModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('ButtonWidgetModel', ButtonWidgetModel);

    var ButtonView = IPython.WidgetView.extend({
      
        // Called when view is rendered.
        render : function(){
            var that = this;
            this.$el = $("<button />")
                .addClass('btn')
                .click(function() {
                    that.model.set('clicks', that.model.get('clicks') + 1)
                });

            this.update(); // Set defaults.
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            this.$el.html(this.model.get('description'));
        },
        
    });

    IPython.notebook.widget_manager.register_widget_view('ButtonView', ButtonView);

});
