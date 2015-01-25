// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/widget",
    "base/js/utils",
    "jquery",
    "bootstrap",
], function(widget, utils, $){

    var DropdownView = widget.DOMWidgetView.extend({
        render : function(){
            /**
             * Called when view is rendered.
             */
            this.$el
                .addClass('widget-hbox widget-dropdown');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-label')
                .hide();
            this.$buttongroup = $('<div />')
                .addClass('widget_item')
                .addClass('btn-group')
                .appendTo(this.$el);
            this.$droplabel = $('<button />')
                .addClass('btn btn-default')
                .addClass('widget-combo-btn')
                .html("&nbsp;")
                .appendTo(this.$buttongroup);
            this.$dropbutton = $('<button />')
                .addClass('btn btn-default')
                .addClass('dropdown-toggle')
                .addClass('widget-combo-carrot-btn')
                .attr('data-toggle', 'dropdown')
                .append($('<span />').addClass("caret"))
                .appendTo(this.$buttongroup);
            this.$droplist = $('<ul />')
                .addClass('dropdown-menu')
                .appendTo(this.$buttongroup);

            this.model.on('change:button_style', function(model, value) {
                this.update_button_style();
            }, this);
            this.update_button_style('');
            
            // Set defaults.
            this.update();
        },
        
        update : function(options){
            /**
             * Update the contents of this view
             *
             * Called when the model is changed.  The model may have been 
             * changed by another view or by a state update from the back-end.
             */

            if (options === undefined || options.updated_view != this) {
                var selected_item_text = this.model.get('value_name');
                if (selected_item_text.trim().length === 0) {
                    this.$droplabel.html("&nbsp;");
                } else {
                    this.$droplabel.text(selected_item_text);
                }
                
                var items = this.model.get('_value_names');
                var $replace_droplist = $('<ul />')
                    .addClass('dropdown-menu');
                // Copy the style
                $replace_droplist.attr('style', this.$droplist.attr('style'));
                var that = this;
                _.each(items, function(item, i) {
                    var item_button = $('<a href="#"/>')
                        .text(item)
                        .on('click', $.proxy(that.handle_click, that));
                    $replace_droplist.append($('<li />').append(item_button));
                });

                this.$droplist.replaceWith($replace_droplist);
                this.$droplist.remove();
                this.$droplist = $replace_droplist;
                
                if (this.model.get('disabled')) {
                    this.$buttongroup.attr('disabled','disabled');
                    this.$droplabel.attr('disabled','disabled');
                    this.$dropbutton.attr('disabled','disabled');
                    this.$droplist.attr('disabled','disabled');
                } else {
                    this.$buttongroup.removeAttr('disabled');
                    this.$droplabel.removeAttr('disabled');
                    this.$dropbutton.removeAttr('disabled');
                    this.$droplist.removeAttr('disabled');
                }

                var description = this.model.get('description');
                if (description.length === 0) {
                    this.$label.hide();
                } else {
                    this.typeset(this.$label, description);
                    this.$label.show();
                }
            }
            return DropdownView.__super__.update.apply(this);
        },

        update_button_style: function(previous_trait_value) {
            var class_map = {
                primary: ['btn-primary'],
                success: ['btn-success'],
                info: ['btn-info'],
                warning: ['btn-warning'],
                danger: ['btn-danger']
            };
            this.update_mapped_classes(class_map, 'button_style', previous_trait_value, this.$droplabel);
            this.update_mapped_classes(class_map, 'button_style', previous_trait_value, this.$dropbutton);
        },

        update_attr: function(name, value) {
            /**
             * Set a css attr of the widget view.
             */
            if (name.substring(0, 6) == 'border' || name == 'background' || name == 'color') {
                this.$droplabel.css(name, value);
                this.$dropbutton.css(name, value);
                this.$droplist.css(name, value);
            } else if (name == 'width') {
                this.$droplist.css(name, value);
                this.$droplabel.css(name, value);
            } else if (name == 'padding') {
                this.$droplist.css(name, value);
                this.$buttongroup.css(name, value);
            } else if (name == 'margin') {
                this.$buttongroup.css(name, value);
            } else if (name == 'height') {
                this.$droplabel.css(name, value);
                this.$dropbutton.css(name, value);
            } else if (name == 'padding' || name == 'margin') {
                this.$el.css(name, value);
            } else {
                this.$droplist.css(name, value);
                this.$droplabel.css(name, value);
            }
        },

        handle_click: function (e) {
            /**
             * Handle when a value is clicked.
             *
             * Calling model.set will trigger all of the other views of the 
             * model to update.
             */
            this.model.set('value_name', $(e.target).text(), {updated_view: this});
            this.touch();

            // Manually hide the droplist.
            e.stopPropagation();
            e.preventDefault();
            this.$buttongroup.removeClass('open');
        },
        
    });


    var RadioButtonsView = widget.DOMWidgetView.extend({    
        render : function(){
            /**
             * Called when view is rendered.
             */
            this.$el
                .addClass('widget-hbox widget-radio');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-label')
                .hide();
            this.$container = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-radio-box');
            this.update();
        },
        
        update : function(options){
            /**
             * Update the contents of this view
             *
             * Called when the model is changed.  The model may have been 
             * changed by another view or by a state update from the back-end.
             */
            if (options === undefined || options.updated_view != this) {
                // Add missing items to the DOM.
                var items = this.model.get('_value_names');
                var disabled = this.model.get('disabled');
                var that = this;
                _.each(items, function(item, index) {
                    var item_query = ' :input[data-value="' + encodeURIComponent(item) + '"]';
                    if (that.$el.find(item_query).length === 0) {
                        var $label = $('<label />')
                            .addClass('radio')
                            .text(item)
                            .appendTo(that.$container);
                        
                        $('<input />')
                            .attr('type', 'radio')
                            .addClass(that.model)
                            .val(item)
                            .attr('data-value', encodeURIComponent(item))
                            .prependTo($label)
                            .on('click', $.proxy(that.handle_click, that));
                    }
                    
                    var $item_element = that.$container.find(item_query);
                    if (that.model.get('value_name') == item) {
                        $item_element.prop('checked', true);
                    } else {
                        $item_element.prop('checked', false);
                    }
                    $item_element.prop('disabled', disabled);
                });
                
                // Remove items that no longer exist.
                this.$container.find('input').each(function(i, obj) {
                    var value = $(obj).val();
                    var found = false;
                    _.each(items, function(item, index) {
                        if (item == value) {
                            found = true;
                            return false;
                        }
                    });
                    
                    if (!found) {
                        $(obj).parent().remove();
                    }
                });

                var description = this.model.get('description');
                if (description.length === 0) {
                    this.$label.hide();
                } else {
                    this.$label.text(description);
                    this.typeset(this.$label, description);
                    this.$label.show();
                }
            }
            return RadioButtonsView.__super__.update.apply(this);
        },

        update_attr: function(name, value) {
            /**
             * Set a css attr of the widget view.
             */
            if (name == 'padding' || name == 'margin') {
                this.$el.css(name, value);
            } else {
                this.$container.css(name, value);
            }
        },

        handle_click: function (e) {
            /**
             * Handle when a value is clicked.
             *
             * Calling model.set will trigger all of the other views of the 
             * model to update.
             */
            this.model.set('value_name', $(e.target).val(), {updated_view: this});
            this.touch();
        },
    });
    

    var ToggleButtonsView = widget.DOMWidgetView.extend({
        initialize: function() {
            this._css_state = {};
            ToggleButtonsView.__super__.initialize.apply(this, arguments);
        },

        render: function() {
            /**
             * Called when view is rendered.
             */
            this.$el
                .addClass('widget-hbox widget-toggle-buttons');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-label')
                .hide();
            this.$buttongroup = $('<div />')
                .addClass('btn-group')
                .appendTo(this.$el);

            this.model.on('change:button_style', function(model, value) {
                this.update_button_style();
            }, this);
            this.update_button_style('');
            this.update();
        },
        
        update : function(options){
            /**
             * Update the contents of this view
             *
             * Called when the model is changed.  The model may have been 
             * changed by another view or by a state update from the back-end.
             */
            if (options === undefined || options.updated_view != this) {
                // Add missing items to the DOM.
                var items = this.model.get('_value_names');
                var disabled = this.model.get('disabled');
                var that = this;
                var item_html;
                _.each(items, function(item, index) {
                    if (item.trim().length === 0) {
                        item_html = "&nbsp;";
                    } else {
                        item_html = utils.escape_html(item);
                    }
                    var item_query = '[data-value="' + encodeURIComponent(item) + '"]';
                    var $item_element = that.$buttongroup.find(item_query);
                    if (!$item_element.length) {
                        $item_element = $('<button/>')
                            .attr('type', 'button')
                            .addClass('btn btn-default')
                            .html(item_html)
                            .appendTo(that.$buttongroup)
                            .attr('data-value', encodeURIComponent(item))
                            .attr('value', item)
                            .on('click', $.proxy(that.handle_click, that));
                        that.update_style_traits($item_element);
                    }
                    if (that.model.get('value_name') == item) {
                        $item_element.addClass('active');
                    } else {
                        $item_element.removeClass('active');
                    }
                    $item_element.prop('disabled', disabled); 
                });
                
                // Remove items that no longer exist.
                this.$buttongroup.find('button').each(function(i, obj) {
                    var value = $(obj).attr('value');
                    var found = false;
                    _.each(items, function(item, index) {
                        if (item == value) {
                            found = true;
                            return false;
                        }
                    });

                    if (!found) {
                        $(obj).remove();
                    }
                });

                var description = this.model.get('description');
                if (description.length === 0) {
                    this.$label.hide();
                } else {
                    this.$label.text();
                    this.typeset(this.$label, description);
                    this.$label.show();
                }
            }
            return ToggleButtonsView.__super__.update.apply(this);
        },

        update_attr: function(name, value) {
            /**
             * Set a css attr of the widget view.
             */
            if (name == 'padding' || name == 'margin') {
                this.$el.css(name, value);
            } else {
                this._css_state[name] = value;
                this.update_style_traits();
            }
        },

        update_style_traits: function(button) {
            for (var name in this._css_state) {
                if (this._css_state.hasOwnProperty(name)) {
                    if (name == 'margin') {
                        this.$buttongroup.css(name, this._css_state[name]);
                    } else if (name != 'width') {
                        if (button) {
                            button.css(name, this._css_state[name]);
                        } else {
                            this.$buttongroup.find('button').css(name, this._css_state[name]);
                        }
                    }
                }
            }
        },

        update_button_style: function(previous_trait_value) {
            var class_map = {
                primary: ['btn-primary'],
                success: ['btn-success'],
                info: ['btn-info'],
                warning: ['btn-warning'],
                danger: ['btn-danger']
            };
            this.update_mapped_classes(class_map, 'button_style', previous_trait_value, this.$buttongroup.find('button'));
        },

        handle_click: function (e) {
            /**
             * Handle when a value is clicked.
             *
             * Calling model.set will trigger all of the other views of the 
             * model to update.
             */
            this.model.set('value_name', $(e.target).attr('value'), {updated_view: this});
            this.touch();
        },    
    });
    

    var SelectView = widget.DOMWidgetView.extend({    
        render : function(){
            /**
             * Called when view is rendered.
             */
            this.$el
                .addClass('widget-hbox widget-select');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-label')
                .hide();
            this.$listbox = $('<select />')
                .addClass('widget-listbox form-control')
                .attr('size', 6)
                .appendTo(this.$el);
            this.update();
        },
        
        update : function(options){
            /**
             * Update the contents of this view
             *
             * Called when the model is changed.  The model may have been 
             * changed by another view or by a state update from the back-end.
             */
            if (options === undefined || options.updated_view != this) {
                // Add missing items to the DOM.
                var items = this.model.get('_value_names');
                var that = this;
                _.each(items, function(item, index) {
                   var item_query = 'option[data-value="' + encodeURIComponent(item) + '"]';
                    if (that.$listbox.find(item_query).length === 0) {
                        $('<option />')
                            .text(item)
                            .attr('data-value', encodeURIComponent(item))
                            .attr('value_name', item)
                            .appendTo(that.$listbox)
                            .on('click', $.proxy(that.handle_click, that));
                    } 
                });

                // Select the correct element
                this.$listbox.val(this.model.get('value_name'));
                
                // Disable listbox if needed
                var disabled = this.model.get('disabled');
                this.$listbox.prop('disabled', disabled);

                // Remove items that no longer exist.
                this.$listbox.find('option').each(function(i, obj) {
                    var value = $(obj).text();
                    var found = false;
                    _.each(items, function(item, index) {
                        if (item == value) {
                            found = true;
                            return false;
                        }
                    });
                    
                    if (!found) {
                        $(obj).remove();
                    }
                });

                var description = this.model.get('description');
                if (description.length === 0) {
                    this.$label.hide();
                } else {
                    this.typeset(this.$label, description);
                    this.$label.show();
                }
            }
            return SelectView.__super__.update.apply(this);
        },

        update_attr: function(name, value) {
            /**
             * Set a css attr of the widget view.
             */
            if (name == 'padding' || name == 'margin') {
                this.$el.css(name, value);
            } else {
                this.$listbox.css(name, value);
            }
        },

        handle_click: function (e) {
            /**
             * Handle when a value is clicked.
             *
             * Calling model.set will trigger all of the other views of the 
             * model to update.
             */
            this.model.set('value_name', $(e.target).text(), {updated_view: this});
            this.touch();
        },    
    });
    
    return {
        'DropdownView': DropdownView,
        'RadioButtonsView': RadioButtonsView,
        'ToggleButtonsView': ToggleButtonsView,
        'SelectView': SelectView,
    };
});
