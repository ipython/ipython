//----------------------------------------------------------------------------
//  Copyright (C) 2013 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// MultiContainerWidget
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 **/

define(["notebook/js/widgets/base"], function(widget_manager){
    var MulticontainerModel = IPython.WidgetModel.extend({});
    widget_manager.register_widget_model('MulticontainerWidgetModel', MulticontainerModel);

    var AccordionView = IPython.WidgetView.extend({
        
        render: function(){
            var guid = 'accordion' + IPython.utils.uuid();
            this.$el
                .attr('id', guid)
                .addClass('accordion');
            this.containers = [];
        },
        
        update: function() {
            // Set tab titles
            var titles = this.model.get('_titles');
            for (var page_index in titles) {

                var accordian = this.containers[page_index];
                if (accordian !== undefined) {
                    accordian
                        .find('.accordion-heading')
                        .find('.accordion-toggle')
                        .html(titles[page_index]);
                }
            }

            // Set selected page
            var selected_index = this.model.get("selected_index");
            if (0 <= selected_index && selected_index < this.containers.length) {
                for (var index in this.containers) {
                    if (index==selected_index) {
                        this.containers[index].find('.accordion-body').collapse('show');    
                    } else {
                        this.containers[index].find('.accordion-body').collapse('hide');    
                    }
                    
                }
            }
            
            return IPython.WidgetView.prototype.update.call(this);
        },

        display_child: function(view) {

            var index = this.containers.length;
            var uuid = IPython.utils.uuid();
            var accordion_group = $('<div />')
                .addClass('accordion-group')
                .appendTo(this.$el);
            var accordion_heading = $('<div />')
                .addClass('accordion-heading')
                .appendTo(accordion_group);
            var that = this;
            var accordion_toggle = $('<a />')
                .addClass('accordion-toggle')
                .attr('data-toggle', 'collapse')
                .attr('data-parent', '#' + this.$el.attr('id'))
                .attr('href', '#' + uuid)
                .click(function(evt){ 
                    that.model.set("selected_index", index);
                    that.model.update_other_views(that);
                 })
                .html('Page ' + index)
                .appendTo(accordion_heading);
            var accordion_body = $('<div />', {id: uuid})
                .addClass('accordion-body collapse')
                .appendTo(accordion_group);
            var accordion_inner = $('<div />')
                .addClass('accordion-inner')
                .appendTo(accordion_body);
            this.containers.push(accordion_group);
            accordion_inner.append(view.$el);

            this.update();

            // Stupid workaround to close the bootstrap accordion tabs which
            // open by default even though they don't have the `in` class
            // attached to them.  For some reason a delay is required.  
            // TODO: Better fix.
            setTimeout(function(){ that.update(); }, 500);
        },
    });

    widget_manager.register_widget_view('AccordionView', AccordionView);
    
    var TabView = IPython.WidgetView.extend({
        
        render: function(){
            var uuid = 'tabs'+IPython.utils.uuid();
            var that = this;
            this.$tabs = $('<div />', {id: uuid})
                .addClass('nav')
                .addClass('nav-tabs')
                .appendTo(this.$el);
            this.$tab_contents = $('<div />', {id: uuid + 'Content'})
                .addClass('tab-content')
                .appendTo(this.$el);

            this.containers = [];
        },

        update: function() {
            // Set tab titles
            var titles = this.model.get('_titles');
            for (var page_index in titles) {
                var tab_text = this.containers[page_index];
                if (tab_text !== undefined) {
                    tab_text.html(titles[page_index]);
                }
            }

            var selected_index = this.model.get('selected_index');
            if (0 <= selected_index && selected_index < this.containers.length) {
                this.select_page(selected_index);
            }

            return IPython.WidgetView.prototype.update.call(this);
        },

        display_child: function(view) {

            var index = this.containers.length;
            var uuid = IPython.utils.uuid();

            var that = this;
            var tab = $('<li />')
                .css('list-style-type', 'none')
                .appendTo(this.$tabs);
            var tab_text = $('<a />')
                .attr('href', '#' + uuid)
                .attr('data-toggle', 'tab') 
                .html('Page ' + index)
                .appendTo(tab)
                .click(function (e) {
                    that.model.set("selected_index", index);
                    that.model.update_other_views(that);
                    that.select_page(index);
                });
            this.containers.push(tab_text);

            var contents_div = $('<div />', {id: uuid})
                .addClass('tab-pane')
                .addClass('fade')
                .append(view.$el)
                .appendTo(this.$tab_contents);

            if (index === 0) {
                tab_text.tab('show');
            }
            this.update();
        },

        select_page: function(index) {
            this.$tabs.find('li')
                .removeClass('active');
            this.containers[index].tab('show');
        },
    });

    widget_manager.register_widget_view('TabView', TabView);
});
