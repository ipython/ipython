// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/widget",
    "base/js/utils",
    "jquery",
    "bootstrap",
], function(widget, utils, $){

    var AccordionView = widget.DOMWidgetView.extend({
        initialize: function(){
            AccordionView.__super__.initialize.apply(this, arguments);

            this.containers = [];
            this.model_containers = {};
            this.children_views = new widget.ViewList(this.add_child_view, this.remove_child_view, this);
            this.listenTo(this.model, 'change:children', function(model, value) {
                this.children_views.update(value);
            }, this);
        },

        render: function(){
            /**
             * Called when view is rendered.
             */
            var guid = 'panel-group' + utils.uuid();
            this.$el
                .attr('id', guid)
                .addClass('panel-group');
            this.model.on('change:selected_index', function(model, value, options) {
                this.update_selected_index(options);
            }, this);
            this.model.on('change:_titles', function(model, value, options) {
                this.update_titles(options);
            }, this);
            this.on('displayed', function() {
                this.update_titles();
            }, this);
            this.children_views.update(this.model.get('children'));
        },

        /**
         * Update the contents of this view
         *
         * Called when the model is changed.  The model may have been 
         * changed by another view or by a state update from the back-end.
         */
        update: function(options) {
            this.update_titles();
            this.update_selected_index(options);
            return TabView.__super__.update.apply(this);
        },

        update_titles: function() {
            /**
             * Set tab titles
             */
            var titles = this.model.get('_titles');
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

        update_selected_index: function(options) {
            /**
             * Only update the selection if the selection wasn't triggered
             * by the front-end.  It must be triggered by the back-end.
             */
            if (options === undefined || options.updated_view != this) {
                var old_index = this.model.previous('selected_index');
                var new_index = this.model.get('selected_index');
                this.containers[old_index].find('.panel-collapse').collapse('hide');
                if (0 <= new_index && new_index < this.containers.length) {
                    this.containers[new_index].find('.panel-collapse').collapse('show');
                }
            }
        },

        remove_child_view: function(view) {
            /**
             * Called when a child is removed from children list.
             * TODO: does this handle two different views of the same model as children?
             */
            var model = view.model;
            var accordion_group = this.model_containers[model.id];
            this.containers.splice(accordion_group.container_index, 1);
            delete this.model_containers[model.id];
            accordion_group.remove();
        },

        add_child_view: function(model) {
            /**
             * Called when a child is added to children list.
             */
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
            
            var dummy = $('<div/>');
            accordion_inner.append(dummy);
            return this.create_child_view(model).then(function(view) {
                dummy.replaceWith(view.$el);
                that.update();
                that.update_titles();

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
            AccordionView.__super__.remove.apply(this, arguments);
            this.children_views.remove();
        },
    });
    

    var TabView = widget.DOMWidgetView.extend({    
        initialize: function() {
            /**
             * Public constructor.
             */
            TabView.__super__.initialize.apply(this, arguments);
            
            this.containers = [];
            this.children_views = new widget.ViewList(this.add_child_view, this.remove_child_view, this);
            this.listenTo(this.model, 'change:children', function(model, value) {
                this.children_views.update(value);
            }, this);
        },

        render: function(){
            /**
             * Called when view is rendered.
             */
            var uuid = 'tabs'+utils.uuid();
            this.$tabs = $('<div />', {id: uuid})
                .addClass('nav')
                .addClass('nav-tabs')
                .appendTo(this.$el);
            this.$tab_contents = $('<div />', {id: uuid + 'Content'})
                .addClass('tab-content')
                .appendTo(this.$el);
            this.children_views.update(this.model.get('children'));
        },

        update_attr: function(name, value) {
            /**
             * Set a css attr of the widget view.
             */
            if (name == 'padding' || name == 'margin') {
                this.$el.css(name, value);
            } else {
                this.$tabs.css(name, value);
            }
        },

        remove_child_view: function(view) {
            /**
             * Called when a child is removed from children list.
             */
            this.containers.splice(view.parent_tab.tab_text_index, 1);
            view.parent_tab.remove();
            view.parent_container.remove();
            view.remove();
        },

        add_child_view: function(model) {
            /**
             * Called when a child is added to children list.
             */
            var index = this.containers.length;
            var uuid = utils.uuid();

            var that = this;
            var tab = $('<li />')
                .css('list-style-type', 'none')
                .appendTo(this.$tabs);

            var tab_text = $('<a />')
                .attr('href', '#' + uuid)
                .attr('data-toggle', 'tab') 
                .text('Page ' + index)
                .appendTo(tab)
                .click(function (e) {
            
                    // Calling model.set will trigger all of the other views of the 
                    // model to update.
                    that.model.set("selected_index", index, {updated_view: that});
                    that.touch();
                    that.select_page(index);
                });
            tab.tab_text_index = that.containers.push(tab_text) - 1;

            var dummy = $('<div />');
            var contents_div = $('<div />', {id: uuid})
                .addClass('tab-pane')
                .addClass('fade')
                .append(dummy)
                .appendTo(that.$tab_contents);

            this.update();
            return this.create_child_view(model).then(function(view) {
                dummy.replaceWith(view.$el);
                view.parent_tab = tab;
                view.parent_container = contents_div;

                // Trigger the displayed event of the child view.
                that.after_displayed(function() {
                    view.trigger('displayed');
                    that.update();
                });
                return view;
            }).catch(utils.reject("Couldn't add child view to box", true));
        },

        update: function(options) {
            /**
             * Update the contents of this view
             *
             * Called when the model is changed.  The model may have been 
             * changed by another view or by a state update from the back-end.
             */
            this.update_titles();
            this.update_selected_index(options);
            return TabView.__super__.update.apply(this);
        },

        /**
         * Updates the tab page titles.
         */
        update_titles: function() {
            var titles = this.model.get('_titles');
            var that = this;
            _.each(titles, function(title, page_index) {
               var tab_text = that.containers[page_index];
                if (tab_text !== undefined) {
                    tab_text.text(title);
                } 
            });
        },

        /**
         * Updates the tab page titles.
         */
        update_selected_index: function(options) {
            if (options === undefined || options.updated_view != this) {
                var selected_index = this.model.get('selected_index');
                if (0 <= selected_index && selected_index < this.containers.length) {
                    this.select_page(selected_index);
                }
            }
        },

        select_page: function(index) {
            /**
             * Select a page.
             */
            this.$tabs.find('li')
                .removeClass('active');
            this.containers[index].tab('show');
        },
        
        remove: function() {
            /**
             * We remove this widget before removing the children as an optimization
             * we want to remove the entire container from the DOM first before
             * removing each individual child separately.
             */
            TabView.__super__.remove.apply(this, arguments);
            this.children_views.remove();
        },
    });

    return {
        'AccordionView': AccordionView,
        'TabView': TabView,
    };
});
