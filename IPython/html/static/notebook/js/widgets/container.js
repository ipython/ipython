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
            this.$el
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


    var ModalView = IPython.WidgetView.extend({
        
        render: function(){
            var that = this;
            this.$el
                .html('')
                .on("remove", function(){
                    that.$window.remove();
                });
            this.$window = $('<div />')
                .addClass('modal widget-modal')
                .appendTo($('#notebook-container'));
            this.$title_bar = $('<div />')
                .addClass('popover-title')
                .appendTo(this.$window);
            var that = this;
            $('<button />')
                .addClass('close')
                .html('&times;')
                .appendTo(this.$title_bar)
                .click(function(){
                    that.hide();
                    event.stopPropagation();
                });
            this.$title = $('<div />')
                .addClass('widget-modal-title')
                .html('&nbsp;')
                .appendTo(this.$title_bar);
            this.$body = $('<div />')
                .addClass('modal-body')
                .addClass('widget-modal-body')
                .addClass('widget-container')
                .appendTo(this.$window);
            
            this.$show_button = $('<button />')
                .html('&nbsp;')
                .addClass('btn btn-info widget-modal-show')
                .appendTo(this.$el)
                .click(function(){
                    that.show();
                });
            
            this.$window.draggable({handle: '.popover-title', snap: '#notebook, .modal', snapMode: 'both'});
            this.$window.resizable();
            this.$window.on('resize', function(){
                that.$body.outerHeight(that.$window.innerHeight() - that.$title_bar.outerHeight());
            })

            this._shown_once = false;
        },
        
        hide: function() {
            this.$window.hide();
            this.$show_button.removeClass('btn-info');
        },
        
        show: function() {
            this.$window.show();
            this.$show_button.addClass('btn-info');
            var position = this.$show_button.offset();
            this.$window.css('left', position.left + this.$show_button.outerWidth());
            this.$window.css('top', position.top);
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
            
            var description = this.model.get('description');
            description = description.replace(/ /g, '&nbsp;', 'm');
            description = description.replace(/\n/g, '<br>\n', 'm');
            if (description.length == 0) {
                this.$title.html('&nbsp;'); // Preserve title height
            } else {
                this.$title.html(description);
            }
            
            var button_text = this.model.get('button_text');
            button_text = button_text.replace(/ /g, '&nbsp;', 'm');
            button_text = button_text.replace(/\n/g, '<br>\n', 'm');
            if (button_text.length == 0) {
                this.$show_button.html('&nbsp;'); // Preserve button height
            } else {
                this.$show_button.html(button_text);
            }
            
            if (!this._shown_once) {
                this._shown_once = true;
                this.show();
            }
            
            return IPython.WidgetView.prototype.update.call(this);
        },

        set_flex_property: function(property_name, enabled) {
            if (enabled) {
                this.$body.addClass(property_name);
            } else {
                this.$body.removeClass(property_name);
            }
        },

        display_child: function(view) {
            this.$body.append(view.$el);
        },
        
        
    });

    widget_manager.register_widget_view('ModalView', ModalView);
});
