define(["notebook/js/widget"], function(){
    var FloatWidgetModel = IPython.WidgetModel.extend({});
    IPython.widget_manager.register_widget_model('FloatWidgetModel', FloatWidgetModel);
});