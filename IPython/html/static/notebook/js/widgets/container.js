require(["notebook/js/widget"], function(){
    var ContainerModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('container_widget', ContainerModel);

    var ContainerView = IPython.WidgetView.extend({
        
        render : function(){
            this.$el = $('<div />')
                .addClass(this.model.comm.comm_id);
        },
        
        update : function(){
            if (this.model.get('vbox')) {
                this.$el.addClass('vbox');
            } else {
                this.$el.removeClass('vbox');
            }
            
            if (this.model.get('hbox')) {
                this.$el.addClass('hbox');
            } else {
                this.$el.removeClass('hbox');
            }
        },
    });

    IPython.notebook.widget_manager.register_widget_view('ContainerView', ContainerView);
});