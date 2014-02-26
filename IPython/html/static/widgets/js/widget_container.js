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

define(["widgets/js/widget"], function(WidgetManager) {

    var ContainerView = IPython.DOMWidgetView.extend({
        render: function(){
            // Called when view is rendered.
            this.$el.addClass('widget-container')
                .addClass('vbox');
            this.children={};
            this.update_children([], this.model.get('_children'));
            this.model.on('change:_children', function(model, value, options) {
                this.update_children(model.previous('_children'), value);
            }, this);
            this.update();
        },
        
        update_children: function(old_list, new_list) {
            // Called when the children list changes.
            this.do_diff(old_list,
                new_list, 
                $.proxy(this.remove_child_model, this),
                $.proxy(this.add_child_model, this));
        },

        remove_child_model: function(model) {
            // Called when a model is removed from the children list.
            this.child_views[model.id].remove();
            this.delete_child_view(model);
        },

        add_child_model: function(model) {
            // Called when a model is added to the children list.
            var view = this.create_child_view(model);
            this.$el.append(view.$el);
        },
        
        update: function(){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            return ContainerView.__super__.update.apply(this);
        },
    });
    
    WidgetManager.register_widget_view('ContainerView', ContainerView);
    
    var PopupView = IPython.DOMWidgetView.extend({
        render: function(){
            // Called when view is rendered.
            var that = this;
            this.children={};
            
            this.$el.on("remove", function(){
                    that.$window.remove();
                });
            this.$window = $('<div />')
                .addClass('modal widget-modal')
                .appendTo($('#notebook-container'))
                .mousedown(function(){
                    that.bring_to_front();
                });

            // Set the elements array since the this.$window element is not child
            // of this.$el and the parent widget manager or other widgets may
            // need to know about all of the top-level widgets.  The IPython
            // widget manager uses this to register the elements with the
            // keyboard manager.
            this.additional_elements = [this.$window]

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
                .html("&nbsp;")
                .appendTo(this.$title_bar);
            this.$body = $('<div />')
                .addClass('modal-body')
                .addClass('widget-modal-body')
                .addClass('widget-container')
                .addClass('vbox')
                .appendTo(this.$window);
            
            this.$show_button = $('<button />')
                .html("&nbsp;")
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

            this.update_children([], this.model.get('_children'));
            this.model.on('change:_children', function(model, value, options) {
                this.update_children(model.previous('_children'), value);
            }, this);
            this.update();
        },
        
        hide: function() {
            // Called when the modal hide button is clicked.
            this.$window.hide();
            this.$show_button.removeClass('btn-info');
        },
        
        show: function() {
            // Called when the modal show button is clicked.
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
            // Make the modal top-most, z-ordered about the other modals.
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
        
        update_children: function(old_list, new_list) {
            // Called when the children list is modified.
            this.do_diff(old_list, 
                new_list, 
                $.proxy(this.remove_child_model, this),
                $.proxy(this.add_child_model, this));
        },

        remove_child_model: function(model) {
            // Called when a child is removed from children list.
            this.child_views[model.id].remove();
            this.delete_child_view(model);
        },

        add_child_model: function(model) {
            // Called when a child is added to children list.
            var view = this.create_child_view(model);
            this.$body.append(view.$el);
        },
        
        update: function(){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            var description = this.model.get('description');
            if (description.trim().length === 0) {
                this.$title.html("&nbsp;"); // Preserve title height
            } else {
                this.$title.text(description);
            }
            
            var button_text = this.model.get('button_text');
            if (button_text.trim().length === 0) {
                this.$show_button.html("&nbsp;"); // Preserve button height
            } else {
                this.$show_button.text(button_text);
            }
            
            if (!this._shown_once) {
                this._shown_once = true;
                this.show();
            }
            
            return PopupView.__super__.update.apply(this);
        },
        
        _get_selector_element: function(selector) {
            // Get an element view a 'special' jquery selector.  (see widget.js)
            //
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
                return PopupView.__super__._get_selector_element.apply(this, [selector]);
            }
        },
    });
    WidgetManager.register_widget_view('PopupView', PopupView);
});
