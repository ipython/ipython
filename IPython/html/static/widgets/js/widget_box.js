// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/widget",
    "jqueryui",
    "base/js/utils",
    "bootstrap",
], function(widget, $, utils){

    var BoxView = widget.DOMWidgetView.extend({
        initialize: function(){
            /**
             * Public constructor
             */
            BoxView.__super__.initialize.apply(this, arguments);
            this.children_views = new widget.ViewList(this.add_child_model, null, this);
            this.listenTo(this.model, 'change:children', function(model, value) {
                this.children_views.update(value);
            }, this);
            this.listenTo(this.model, 'change:overflow_x', function(model, value) {
                this.update_overflow_x();
            }, this);
            this.listenTo(this.model, 'change:overflow_y', function(model, value) {
                this.update_overflow_y();
            }, this);
            this.listenTo(this.model, 'change:box_style', function(model, value) {
                this.update_box_style();
            }, this);
        },

        update_attr: function(name, value) {
            /**
             * Set a css attr of the widget view.
             */
            this.$box.css(name, value);
        },

        render: function(){
            /**
             * Called when view is rendered.
             */
            this.$box = this.$el;
            this.$box.addClass('widget-box');
            this.children_views.update(this.model.get('children'));
            this.update_overflow_x();
            this.update_overflow_y();
            this.update_box_style('');
        },

        update_overflow_x: function() {
            /**
             * Called when the x-axis overflow setting is changed.
             */
            this.$box.css('overflow-x', this.model.get('overflow_x'));
        },

        update_overflow_y: function() {
            /**
             * Called when the y-axis overflow setting is changed.
             */
            this.$box.css('overflow-y', this.model.get('overflow_y'));
        },

        update_box_style: function(previous_trait_value) {
            var class_map = {
                success: ['alert', 'alert-success'],
                info: ['alert', 'alert-info'],
                warning: ['alert', 'alert-warning'],
                danger: ['alert', 'alert-danger']
            };
            this.update_mapped_classes(class_map, 'box_style', previous_trait_value, this.$box);
        },
        
        add_child_model: function(model) {
            /**
             * Called when a model is added to the children list.
             */
            var that = this;
            var dummy = $('<div/>');
            that.$box.append(dummy);
            return this.create_child_view(model).then(function(view) {
                dummy.replaceWith(view.el);

                // Trigger the displayed event of the child view.
                that.after_displayed(function() {
                    view.trigger('displayed');
                });
                return view;
            }).catch(utils.reject("Couldn't add child view to box", true));
        },
        
        remove: function() {
            /**
             * We remove this widget before removing the children as an optimization
             * we want to remove the entire container from the DOM first before
             * removing each individual child separately.
             */
            BoxView.__super__.remove.apply(this, arguments);
            this.children_views.remove();
        },
    });


    var FlexBoxView = BoxView.extend({
        render: function(){
            FlexBoxView.__super__.render.apply(this);
            this.listenTo(this.model, 'change:orientation', this.update_orientation, this);
            this.listenTo(this.model, 'change:flex', this._flex_changed, this);
            this.listenTo(this.model, 'change:pack', this._pack_changed, this);
            this.listenTo(this.model, 'change:align', this._align_changed, this);
            this._flex_changed();
            this._pack_changed();
            this._align_changed();
            this.update_orientation();
        },

        update_orientation: function(){
            var orientation = this.model.get("orientation");
            if (orientation == "vertical") {
                this.$box.removeClass("hbox").addClass("vbox");
            } else {
                this.$box.removeClass("vbox").addClass("hbox");
            }
        },

        _flex_changed: function(){
            if (this.model.previous('flex')) {
                this.$box.removeClass('box-flex' + this.model.previous('flex'));
            }
            this.$box.addClass('box-flex' + this.model.get('flex'));
        },

        _pack_changed: function(){
            if (this.model.previous('pack')) {
                this.$box.removeClass(this.model.previous('pack'));
            }
            this.$box.addClass(this.model.get('pack'));
        },

        _align_changed: function(){
            if (this.model.previous('align')) {
                this.$box.removeClass('align-' + this.model.previous('align'));
            }
            this.$box.addClass('align-' + this.model.get('align'));
        },
    });

    var PopupView = BoxView.extend({

        render: function(){
            /**
             * Called when view is rendered.
             */
            var that = this;
            
            this.$el.on("remove", function(){
                    that.$backdrop.remove();
                });
            this.$backdrop = $('<div />')
                .appendTo($('#notebook-container'))
                .addClass('modal-dialog')
                .css('position', 'absolute')
                .css('left', '0px')
                .css('top', '0px');
            this.$window = $('<div />')
                .appendTo(this.$backdrop)
                .addClass('modal-content widget-modal')
                .mousedown(function(){
                    that.bring_to_front();
                });

            // Set the elements array since the this.$window element is not child
            // of this.$el and the parent widget manager or other widgets may
            // need to know about all of the top-level widgets.  The IPython
            // widget manager uses this to register the elements with the
            // keyboard manager.
            this.additional_elements = [this.$window];

            this.$title_bar = $('<div />')
                .addClass('popover-title')
                .appendTo(this.$window)
                .mousedown(function(){
                    that.bring_to_front();
                });
            this.$close = $('<button />')
                .addClass('close fa fa-remove')
                .css('margin-left', '5px')
                .appendTo(this.$title_bar)
                .click(function(){
                    that.hide();
                    event.stopPropagation();
                });
            this.$minimize = $('<button />')
                .addClass('close fa fa-arrow-down')
                .appendTo(this.$title_bar)
                .click(function(){
                    that.popped_out = !that.popped_out;
                    if (!that.popped_out) {
                        that.$minimize
                            .removeClass('fa-arrow-down')
                            .addClass('fa-arrow-up');
                            
                        that.$window
                            .draggable('destroy')
                            .resizable('destroy')
                            .removeClass('widget-modal modal-content')
                            .addClass('docked-widget-modal')
                            .detach()
                            .insertBefore(that.$show_button);
                        that.$show_button.hide();
                        that.$close.hide();
                    } else {
                        that.$minimize
                            .addClass('fa-arrow-down')
                            .removeClass('fa-arrow-up');

                        that.$window
                            .removeClass('docked-widget-modal')
                            .addClass('widget-modal modal-content')
                            .detach()
                            .appendTo(that.$backdrop)
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
            this.$box = $('<div />')
                .addClass('modal-body')
                .addClass('widget-modal-body')
                .addClass('widget-box')
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
                that.$box.outerHeight(that.$window.innerHeight() - that.$title_bar.outerHeight());
            });

            this._shown_once = false;
            this.popped_out = true;

            this.children_views.update(this.model.get('children'))
        },
        
        hide: function() {
            /**
             * Called when the modal hide button is clicked.
             */
            this.$window.hide();
            this.$show_button.removeClass('btn-info');
        },
        
        show: function() {
            /**
             * Called when the modal show button is clicked.
             */
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
            /**
             * Make the modal top-most, z-ordered about the other modals.
             */
            var $widget_modals = $(".widget-modal");
            var max_zindex = 0;
            $widget_modals.each(function (index, el){
                var zindex = parseInt($(el).css('z-index'));
                if (!isNaN(zindex)) {
                    max_zindex = Math.max(max_zindex, zindex);
                }
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
            /**
             * Update the contents of this view
             *
             * Called when the model is changed.  The model may have been 
             * changed by another view or by a state update from the back-end.
             */
            var description = this.model.get('description');
            if (description.trim().length === 0) {
                this.$title.html("&nbsp;"); // Preserve title height
            } else {
                this.typeset(this.$title, description);
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
            /**
             * Get an element view a 'special' jquery selector.  (see widget.js)
             *
             * Since the modal actually isn't within the $el in the DOM, we need to extend
             * the selector logic to allow the user to set css on the modal if need be.
             * The convention used is:
             * "modal" - select the modal div
             * "modal [selector]" - select element(s) within the modal div.
             * "[selector]" - select elements within $el
             * "" - select the $el
             */
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

    return {
        'BoxView': BoxView,
        'PopupView': PopupView,
        'FlexBoxView': FlexBoxView,
    };
});
