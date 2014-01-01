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

define(["notebook/js/widgets/base"], function(widget_manager) {

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
            this.children={};
            this.update_children([], this.model.get('children'));
            this.model.on('change:children', function(model, value, options) {
                this.update_children(model.previous('children'), value);
            }, this);
            this.update()
        },
        
        update_children: function(old_list, new_list) {
            this.$el.empty();
            this.update_child_views(old_list, new_list);
            _.each(new_list, function(element, index, list) {
                this.$el.append(this.child_views[element].$el);
            }, this)
        },
        
        update: function(){
            set_flex_properties(this, this.$el);
            return IPython.WidgetView.prototype.update.call(this);
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
                .appendTo($('#notebook-container'))
                .mousedown(function(){
                    that.bring_to_front();
                });
            this.$title_bar = $('<div />')
                .addClass('popover-title')
                .appendTo(this.$window)
                .mousedown(function(){
                    that.bring_to_front();
                });
            this.$close = $('<button />')
                .addClass('close icon-remove')
                .css('margin-left', '5px')
                .appendTo(this.$title_bar)
                .click(function(){
                    that.hide();
                    event.stopPropagation();
                });
            this.$minimize = $('<button />')
                .addClass('close icon-arrow-down')
                .appendTo(this.$title_bar)
                .click(function(){
                    that.popped_out = !that.popped_out;
                    if (!that.popped_out) {
                        that.$minimize
                            .removeClass('icon-arrow-down')
                            .addClass('icon-arrow-up');
                            
                        that.$window
                            .draggable('destroy')
                            .resizable('destroy')
                            .removeClass('widget-modal modal')
                            .addClass('docked-widget-modal')
                            .detach()
                            .insertBefore(that.$show_button);
                        that.$show_button.hide();
                        that.$close.hide();
                    } else {
                        that.$minimize
                            .addClass('icon-arrow-down')
                            .removeClass('icon-arrow-up');

                        that.$window
                            .removeClass('docked-widget-modal')
                            .addClass('widget-modal modal')
                            .detach()
                            .appendTo($('#notebook-container'))
                            .draggable({handle: '.popover-title', snap: '#notebook, .modal', snapMode: 'both'})
                            .resizable()
                            .children('.ui-resizable-handle').show();
                        that.show();
                        that.$show_button.show();
                        that.$close.show();
                    }
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
            });

            this.$el_to_style = this.$body;
            this._shown_once = false;
            this.popped_out = true;
        },
        
        hide: function() {
            this.$window.hide();
            this.$show_button.removeClass('btn-info');
        },
        
        show: function() {
            this.$show_button.addClass('btn-info');

            this.$window.show();
            if (this.popped_out) {
                this.$window.css("positon", "absolute");
                this.$window.css("top", "0px");
                this.$window.css("left", Math.max(0, (($('body').outerWidth() - this.$window.outerWidth()) / 2) + 
                    $(window).scrollLeft()) + "px");
                this.bring_to_front();
            }
        },
        
        bring_to_front: function() {
            var $widget_modals = $(".widget-modal");
            var max_zindex = 0;
            $widget_modals.each(function (index, el){
                max_zindex = Math.max(max_zindex, parseInt($(el).css('z-index')));
            });
            
            // Start z-index of widget modals at 2000
            max_zindex = Math.max(max_zindex, 2000);

            $widget_modals.each(function (index, el){
                $el = $(el);
                if (max_zindex == parseInt($el.css('z-index'))) {
                    $el.css('z-index', max_zindex - 1);
                }
            });
            this.$window.css('z-index', max_zindex);
        },
        
        update: function(){
            set_flex_properties(this, this.$body);
            
            var description = this.model.get('description');
            description = description.replace(/ /g, '&nbsp;', 'm');
            description = description.replace(/\n/g, '<br>\n', 'm');
            if (description.length === 0) {
                this.$title.html('&nbsp;'); // Preserve title height
            } else {
                this.$title.html(description);
            }
            
            var button_text = this.model.get('button_text');
            button_text = button_text.replace(/ /g, '&nbsp;', 'm');
            button_text = button_text.replace(/\n/g, '<br>\n', 'm');
            if (button_text.length === 0) {
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
