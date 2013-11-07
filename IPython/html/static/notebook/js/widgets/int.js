define(["notebook/js/widget"], function(){
    var IntWidgetModel = IPython.WidgetModel.extend({});
    IPython.widget_manager.register_widget_model('IntWidgetModel', IntWidgetModel);
});