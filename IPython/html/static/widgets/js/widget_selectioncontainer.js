// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/widget",
    "base/js/utils",
    "jquery",
    "bootstrap",
], function(widget, utils, $){

    var AccordionView = widget.DOMWidgetView.extend({
        render: function(){
            // Called when view is rendered.
            var guid = 'panel-group' + utils.uuid();
            this.$el
                .attr('id', guid)
                .addClass('panel-group');
            this.containers = [];
            this.model_containers = {};
            this.update_children([], this.model.get('children'));
            this.model.on('change:children', function(model, value, options) {
                this.update_children(model.previous('children'), value);
            }, this);
            this.model.on('change:selected_index', function(model, value, options) {
                this.update_selected_index(model.previous('selected_index'), value, options);
            }, this);
            this.model.on('change:_titles', function(model, value, options) {
                this.update_titles(value);
            }, this);
            var that = this;
            this.on('displayed', function() {
                this.update_titles();
            }, this);
        },

        update_titles: function(titles) {
            // Set tab titles
            if (!titles) {
                titles = this.model.get('_titles');
            }

            var that = this;
            _.each(titles, function(title, page_index) {
                var accordian = that.containers[page_index];
                if (accordian !== undefined) {
                    accordian
                        .find('.panel-heading')
                        .find('.accordion-toggle')
                        .text(title);
                }
            });
        },

        update_selected_index: function(old_index, new_index, options) {
            // Only update the selection if the selection wasn't triggered
            // by the front-end.  It must be triggered by the back-end.
            if (options === undefined || options.updated_view != this) {
                this.containers[old_index].find('.panel-collapse').collapse('hide');
                if (0 <= new_index && new_index < this.containers.length) {
                    this.containers[new_index].find('.panel-collapse').collapse('show');
                }
            }
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
            var accordion_group = this.model_containers[model.id];
            this.containers.splice(accordion_group.container_index, 1);
            delete this.model_containers[model.id];
            accordion_group.remove();
            this.pop_child_view(model);
        },

        add_child_model: function(model) {
            // Called when a child is added to children list.
            var view = this.create_child_view(model);
            var index = this.containers.length;
            var uuid = utils.uuid();
            var accordion_group = $('<div />')
                .addClass('panel panel-default')
                .appendTo(this.$el);
            var accordion_heading = $('<div />')
                .addClass('panel-heading')
                .appendTo(accordion_group);
            var that = this;
            var accordion_toggle = $('<a />')
                .addClass('accordion-toggle')
                .attr('data-toggle', 'collapse')
                .attr('data-parent', '#' + this.$el.attr('id'))
                .attr('href', '#' + uuid)
                .click(function(evt){ 
            
                    // Calling model.set will trigger all of the other views of the 
                    // model to update.
                    that.model.set("selected_index", index, {updated_view: that});
                    that.touch();
                 })
                .text('Page ' + index)
                .appendTo(accordion_heading);
            var accordion_body = $('<div />', {id: uuid})
                .addClass('panel-collapse collapse')
                .appendTo(accordion_group);
            var accordion_inner = $('<div />')
                .addClass('panel-body')
                .appendTo(accordion_body);
            var container_index = this.containers.push(accordion_group) - 1;
            accordion_group.container_index = container_index;
            this.model_containers[model.id] = accordion_group;
            accordion_inner.append(view.$el);

            this.update();
            this.update_titles();

            // Trigger the displayed event of the child view.
            this.after_displayed(function() {
                view.trigger('displayed');
            });
        },
    });
    

    var TabView = widget.DOMWidgetView.extend({    
        initialize: function() {
            // Public constructor.
            this.containers = [];
            TabView.__super__.initialize.apply(this, arguments);
        },

        render: function(){
            // Called when view is rendered.
            var uuid = 'tabs'+utils.uuid();
            var that = this;
            this.$tabs = $('<div />', {id: uuid})
                .addClass('nav')
                .addClass('nav-tabs')
                .appendTo(this.$el);
            this.$tab_contents = $('<div />', {id: uuid + 'Content'})
                .addClass('tab-content')
                .appendTo(this.$el);
            this.containers = [];
            this.update_children([], this.model.get('children'));
            this.model.on('change:children', function(model, value, options) {
                this.update_children(model.previous('children'), value);
            }, this);
        },

        update_attr: function(name, value) {
            // Set a css attr of the widget view.
            this.$tabs.css(name, value);
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
            var view = this.pop_child_view(model);
            this.containers.splice(view.parent_tab.tab_text_index, 1);
            view.parent_tab.remove();
            view.parent_container.remove();
            view.remove();
        },

        add_child_model: function(model) {
            // Called when a child is added to children list.
            var view = this.create_child_view(model);
            var index = this.containers.length;
            var uuid = utils.uuid();

            var that = this;
            var tab = $('<li />')
                .css('list-style-type', 'none')
                .appendTo(this.$tabs);
            view.parent_tab = tab;

            var tab_text = $('<a />')
                .attr('href', '#' + uuid)
                .attr('data-toggle', 'tab') 
                .text('Page ' + index)
                .appendTo(tab)
                .click(function (e) {
            
                    // Calling model.set will trigger all of the other views of the 
                    // model to update.
                    that.model.set("selected_index", index, {updated_view: this});
                    that.touch();
                    that.select_page(index);
                });
            tab.tab_text_index = this.containers.push(tab_text) - 1;

            var contents_div = $('<div />', {id: uuid})
                .addClass('tab-pane')
                .addClass('fade')
                .append(view.$el)
                .appendTo(this.$tab_contents);
            view.parent_container = contents_div;

            // Trigger the displayed event of the child view.
            this.after_displayed(function() {
                view.trigger('displayed');
            });
        },

        update: function(options) {
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            if (options === undefined || options.updated_view != this) {
                // Set tab titles
                var titles = this.model.get('_titles');
                var that = this;
                _.each(titles, function(title, page_index) {
                   var tab_text = that.containers[page_index];
                    if (tab_text !== undefined) {
                        tab_text.text(title);
                    } 
                });

                var selected_index = this.model.get('selected_index');
                if (0 <= selected_index && selected_index < this.containers.length) {
                    this.select_page(selected_index);
                }
            }
            return TabView.__super__.update.apply(this);
        },

        select_page: function(index) {
            // Select a page.
            this.$tabs.find('li')
                .removeClass('active');
            this.containers[index].tab('show');
        },
    });

    return {
        'AccordionView': AccordionView,
        'TabView': TabView,
    };
});
