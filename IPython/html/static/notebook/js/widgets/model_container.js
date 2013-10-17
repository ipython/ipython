require(["notebook/js/widget"], function () {
    var ContainerModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('container_widget', ContainerModel);

    var ContainerView = IPython.WidgetView.extend({
        
        render : function(){
            this.$el.html('');
            this.$container = $('<div />')
                .addClass('container')
                .addClass(this.model.comm.comm_id);
            this.$el.append(this.$container);
        },
        
        update : function(){},
    });

    IPython.notebook.widget_manager.register_widget_view('ContainerView', ContainerView);
});