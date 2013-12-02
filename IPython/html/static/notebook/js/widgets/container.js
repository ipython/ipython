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

    var set_flex_property = function(element, property_name, enabled) {
        if (enabled) {
            element.addClass(property_name);
        } else {
            element.removeClass(property_name);
        }
    };

    var set_flex_properties = function(context, element) {

        // Apply flexible box model properties by adding and removing
        // corrosponding CSS classes.
        // Defined in IPython/html/static/base/less/flexbox.less
        set_flex_property(element, 'vbox', context.model.get('_vbox'));
        set_flex_property(element, 'hbox', context.model.get('_hbox'));
        set_flex_property(element, 'start', context.model.get('_pack_start'));
        set_flex_property(element, 'center', context.model.get('_pack_center'));
        set_flex_property(element, 'end', context.model.get('_pack_end'));
        set_flex_property(element, 'align-start', context.model.get('_align_start'));
        set_flex_property(element, 'align-center', context.model.get('_align_center'));
        set_flex_property(element, 'align-end', context.model.get('_align_end'));
        set_flex_property(element, 'box-flex0', context.model.get('_flex0'));
        set_flex_property(element, 'box-flex1', context.model.get('_flex1'));
        set_flex_property(element, 'box-flex2', context.model.get('_flex2'));
    };



    var ContainerModel = IPython.WidgetModel.extend({});
    widget_manager.register_widget_model('ContainerWidgetModel', ContainerModel);

    var ContainerView = IPython.WidgetView.extend({
        
        render: function(){
            this.$el
                .addClass('widget-container');
        },
        
        update: function(){
            set_flex_properties(this, this.$el);
            return IPython.WidgetView.prototype.update.call(this);
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

            this.$el_to_style = this.$body;
            this._shown_once = false;
        },
        
        hide: function() {
            this.$window.hide();
            this.$show_button.removeClass('btn-info');
        },
        
        show: function() {
            this.$show_button.addClass('btn-info');

            this.$window.show();
            this.$window.css("positon", "absolute")
            this.$window.css("top", "0px");
            this.$window.css("left", Math.max(0, (($('body').outerWidth() - this.$window.outerWidth()) / 2) + 
                $(window).scrollLeft()) + "px");
        },
        
        update: function(){
            set_flex_properties(this, this.$body);
            
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

        display_child: function(view) {
            this.$body.append(view.$el);
        },
        
        _get_selector_element: function(selector) {

            // Since the modal actually isn't within the $el in the DOM, we need to extend
            // the selector logic to allow the user to set css on the modal if need be.
            // The convention used is:
            // "modal" - select the modal div
            // "modal [selector]" - select element(s) within the modal div.
            // "[selector]" - select elements within $el
            // "" - select the $el_to_style
            if (selector.substring(0, 5) == 'modal') {
                if (selector == 'modal') {
                    return this.$window;
                } else {
                    return this.$window.find(selector.substring(6));
                }
            } else {
                return IPython.WidgetView.prototype._get_selector_element.call(this, selector);
            }
        },
        
    });

    widget_manager.register_widget_view('ModalView', ModalView);
});
