require(["../static/notebook/js/widget"], function(){
    var ContainerModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('ContainerWidgetModel', ContainerModel);

    var ContainerView = IPython.WidgetView.extend({
        
        render : function(){
            this.$el = $('<div />')
                .addClass('widget_container');
        },
        
        update : function(){

            // Apply flexible box model properties by adding and removing
            // corrosponding CSS classes.
            // Defined in IPython/html/static/base/less/flexbox.less
            var flex_properties = ['vbox', 'hbox', 'center', 'end', 'center'];
            for (var index in flex_properties) {
                if (this.model.get('_' + flex_properties[index])) {
                    this.$el.addClass(flex_properties[index]);
                } else {
                    this.$el.removeClass(flex_properties[index]);
                }    
            }
            return IPython.WidgetView.prototype.update.call(this);
        },

        display_child : function(view) {
            this.$el.append(view.$el);
        },
    });

    IPython.notebook.widget_manager.register_widget_view('ContainerView', ContainerView);
});