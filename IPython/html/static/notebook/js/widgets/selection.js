//----------------------------------------------------------------------------
//  Copyright (C) 2013 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// SelectionWidget
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 **/

define(["notebook/js/widget"], function(widget_manager){
    var SelectionWidgetModel = IPython.WidgetModel.extend({});
    widget_manager.register_widget_model('SelectionWidgetModel', SelectionWidgetModel);

    var DropdownView = IPython.WidgetView.extend({
        
        // Called when view is rendered.
        render : function(){
            
            this.$el
                .addClass('widget-hbox-single')
                .html('');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-hlabel')
                .hide();
            this.$buttongroup = $('<div />')
                .addClass('widget_item')
                .addClass('btn-group')
                .appendTo(this.$el);
            this.$el_to_style = this.$buttongroup; // Set default element to style
            this.$droplabel = $('<button />')
                .addClass('btn')
                .addClass('widget-combo-btn')
                .html('&nbsp;')
                .appendTo(this.$buttongroup);
            this.$dropbutton = $('<button />')
                .addClass('btn')
                .addClass('dropdown-toggle')
                .addClass('widget-combo-carrot-btn')
                .attr('data-toggle', 'dropdown')
                .html('<span class="caret"></span>')
                .appendTo(this.$buttongroup);
            this.$droplist = $('<ul />')
                .addClass('dropdown-menu')
                .appendTo(this.$buttongroup);
            
            // Set defaults.
            this.update();
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){

            var selected_item_text = this.model.get('value');
            selected_item_text = selected_item_text.replace(/ /g, '&nbsp;');
            selected_item_text = selected_item_text.replace(/\n/g, '<br>\n');
            if (selected_item_text.length == 0) {
                this.$droplabel.html('&nbsp;');
            } else {
                this.$droplabel.html(selected_item_text);    
            }
            
            var items = this.model.get('values');
            this.$droplist.html('');
            for (var index in items) {
                var that = this;
                var item_button = $('<a href="#"/>')
                    .html(items[index])
                    .on('click', function(e){
                        that.model.set('value', $(e.target).html(), this);
                        that.model.update_other_views(that);
                    })
                
                this.$droplist.append($('<li />').append(item_button))
            }
            
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
            if (description.length == 0) {
                this.$label.hide();
            } else {
                this.$label.html(description);
                this.$label.show();
            }
            return IPython.WidgetView.prototype.update.call(this);
        },
        
    });

    widget_manager.register_widget_view('DropdownView', DropdownView);

    var RadioButtonsView = IPython.WidgetView.extend({
        
        // Called when view is rendered.
        render : function(){
            this.$el
                .addClass('widget-hbox')
                .html('');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-hlabel')
                .hide();
            this.$container = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-container')
                .addClass('vbox');
            this.$el_to_style = this.$container; // Set default element to style
            this.update();
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            
            // Add missing items to the DOM.
            var items = this.model.get('values');
            var disabled = this.model.get('disabled');
            for (var index in items) {
                var item_query = ' :input[value="' + items[index] + '"]';
                if (this.$el.find(item_query).length == 0) {
                    var $label = $('<label />')
                        .addClass('radio')
                        .html(items[index])
                        .appendTo(this.$container);
                    
                    var that = this;
                    $('<input />')
                        .attr('type', 'radio')
                        .addClass(this.model)
                        .val(items[index])
                        .prependTo($label)
                        .on('click', function(e){
                            that.model.set('value', $(e.target).val(), this);
                            that.model.update_other_views(that);
                        });
                }
                
                var $item_element = this.$container.find(item_query);
                if (this.model.get('value') == items[index]) {
                    $item_element.prop('checked', true);
                } else {
                    $item_element.prop('checked', false);
                }
                $item_element.prop('disabled', disabled);
            }
            
            // Remove items that no longer exist.
            this.$container.find('input').each(function(i, obj) {
                var value = $(obj).val();
                var found = false;
                for (var index in items) {
                    if (items[index] == value) {
                        found = true;
                        break;
                    }
                }
                
                if (!found) {
                    $(obj).parent().remove();
                }
            });

            var description = this.model.get('description');
            if (description.length == 0) {
                this.$label.hide();
            } else {
                this.$label.html(description);
                this.$label.show();
            }
            return IPython.WidgetView.prototype.update.call(this);
        },
        
    });

    widget_manager.register_widget_view('RadioButtonsView', RadioButtonsView);


    var ToggleButtonsView = IPython.WidgetView.extend({
        
        // Called when view is rendered.
        render : function(){
            this.$el
                .addClass('widget-hbox-single')
                .html('');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-hlabel')
                .hide();
            this.$buttongroup = $('<div />')
                .addClass('btn-group')
                .attr('data-toggle', 'buttons-radio')
                .appendTo(this.$el);
            this.$el_to_style = this.$buttongroup; // Set default element to style
            this.update();
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            
            // Add missing items to the DOM.
            var items = this.model.get('values');
            var disabled = this.model.get('disabled');
            for (var index in items) {
                var item_query = ' :contains("' + items[index] + '")';
                if (this.$buttongroup.find(item_query).length == 0) {
                    
                    var that = this;
                    $('<button />')
                        .attr('type', 'button')
                        .addClass('btn')
                        .html(items[index])
                        .appendTo(this.$buttongroup)
                        .on('click', function(e){
                            that.model.set('value', $(e.target).html(), this);
                            that.model.update_other_views(that);
                        });
                }
                
                var $item_element = this.$buttongroup.find(item_query);
                if (this.model.get('value') == items[index]) {
                    $item_element.addClass('active');
                } else {
                    $item_element.removeClass('active');
                }
                $item_element.prop('disabled', disabled);
            }
            
            // Remove items that no longer exist.
            this.$buttongroup.find('button').each(function(i, obj) {
                var value = $(obj).html();
                var found = false;
                for (var index in items) {
                    if (items[index] == value) {
                        found = true;
                        break;
                    }
                }
                
                if (!found) {
                    $(obj).remove();
                }
            });

            var description = this.model.get('description');
            if (description.length == 0) {
                this.$label.hide();
            } else {
                this.$label.html(description);
                this.$label.show();
            }
            return IPython.WidgetView.prototype.update.call(this);
        },
        
    });

    widget_manager.register_widget_view('ToggleButtonsView', ToggleButtonsView);

    var ListBoxView = IPython.WidgetView.extend({
        
        // Called when view is rendered.
        render : function(){
            this.$el
                .addClass('widget-hbox')
                .html('');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-hlabel')
                .hide();
            this.$listbox = $('<select />')
                .addClass('widget-listbox')
                .attr('size', 6)
                .appendTo(this.$el);
            this.$el_to_style = this.$listbox; // Set default element to style
            this.update();
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            
            // Add missing items to the DOM.
            var items = this.model.get('values');
            for (var index in items) {
                var item_query = ' :contains("' + items[index] + '")';
                if (this.$listbox.find(item_query).length == 0) {
                    
                    var that = this;
                    $('<option />')
                        .html(items[index])
                        .attr('value', items[index])
                        .appendTo(this.$listbox)
                        .on('click', function(e){
                            that.model.set('value', $(e.target).html(), this);
                            that.model.update_other_views(that);
                        });
                }
            }

            // Select the correct element
            this.$listbox.val(this.model.get('value'));
            
            // Disable listbox if needed
            var disabled = this.model.get('disabled');
            this.$listbox.prop('disabled', disabled);

            // Remove items that no longer exist.
            this.$listbox.find('option').each(function(i, obj) {
                var value = $(obj).html();
                var found = false;
                for (var index in items) {
                    if (items[index] == value) {
                        found = true;
                        break;
                    }
                }
                
                if (!found) {
                    $(obj).remove();
                }
            });

            var description = this.model.get('description');
            if (description.length == 0) {
                this.$label.hide();
            } else {
                this.$label.html(description);
                this.$label.show();
            }
            return IPython.WidgetView.prototype.update.call(this);
        },
        
    });

    widget_manager.register_widget_view('ListBoxView', ListBoxView);
});
