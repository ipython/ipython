//----------------------------------------------------------------------------
//  Copyright (C) 2013 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// ContainerWidget
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 **/

define(["notebook/js/widget"], function(widget_manager) {
    var ContainerModel = IPython.WidgetModel.extend({});
    widget_manager.register_widget_model('ContainerWidgetModel', ContainerModel);

    var ContainerView = IPython.WidgetView.extend({
        
        render: function(){
            this.$el =
                .addClass('widget-container');
        },
        
        update: function(){

            // Apply flexible box model properties by adding and removing
            // corrosponding CSS classes.
            // Defined in IPython/html/static/base/less/flexbox.less
            this.set_flex_property('vbox', this.model.get('_vbox'));
            this.set_flex_property('hbox', this.model.get('_hbox'));
            this.set_flex_property('start', this.model.get('_pack_start'));
            this.set_flex_property('center', this.model.get('_pack_center'));
            this.set_flex_property('end', this.model.get('_pack_end'));
            this.set_flex_property('align-start', this.model.get('_align_start'));
            this.set_flex_property('align-center', this.model.get('_align_center'));
            this.set_flex_property('align-end', this.model.get('_align_end'));
            this.set_flex_property('box-flex0', this.model.get('_flex0'));
            this.set_flex_property('box-flex1', this.model.get('_flex1'));
            this.set_flex_property('box-flex2', this.model.get('_flex2'));

            return IPython.WidgetView.prototype.update.call(this);
        },

        set_flex_property: function(property_name, enabled) {
            if (enabled) {
                this.$el.addClass(property_name);
            } else {
                this.$el.removeClass(property_name);
            }
        },

        display_child: function(view) {
            this.$el.append(view.$el);
        },
    });

    widget_manager.register_widget_view('ContainerView', ContainerView);
});