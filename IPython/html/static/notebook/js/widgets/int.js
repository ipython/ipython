require(["../static/notebook/js/widget"], function(){
    var IntWidgetModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('IntWidgetModel', IntWidgetModel);
});