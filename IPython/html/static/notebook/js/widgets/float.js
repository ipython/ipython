require(["../static/notebook/js/widget"], function(){
    var FloatWidgetModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('FloatWidgetModel', FloatWidgetModel);
});