require(["notebook/js/widget"], function(){
    var MulticontainerModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('MulticontainerWidgetModel', MulticontainerModel);

    var AccordionView = IPython.WidgetView.extend({
        
        render: function(){
            this.$el = $('<div />', {id: IPython.utils.uuid()})
                .addClass('accordion');
            this.containers = [];
        },
        
        update: function() {
            // Set tab titles
            var titles = this.model.get('_titles');
            for (var page_index in titles) {

                var accordian = this.containers[page_index]
                if (accordian != undefined) {
                    accordian
                        .find('.accordion-heading')
                        .find('.accordion-toggle')
                        .html(titles[page_index]);
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
            var accordion_toggle = $('<a />')
                .addClass('accordion-toggle')
                .attr('data-toggle', 'collapse')
                .attr('data-parent', '#' + this.$el.attr('id'))
                .attr('href', '#' + uuid)
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
        },
    });

    IPython.notebook.widget_manager.register_widget_view('AccordionView', AccordionView);
    
    var TabView = IPython.WidgetView.extend({
        
        render: function(){
            this.$el = $('<div />');
            var uuid = IPython.utils.uuid();
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
                var tab_text = this.containers[page_index]
                if (tab_text != undefined) {
                    tab_text.html(titles[page_index]);
                }
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
                    that.$tabs.find('li')
                        .removeClass('active');
                });
            this.containers.push(tab_text);

            var contents_div = $('<div />', {id: uuid})
                .addClass('tab-pane')
                .addClass('fade')
                .append(view.$el)
                .appendTo(this.$tab_contents);

            if (index==0) {
                tab_text.tab('show');
            }
            this.update();
        },
    });

    IPython.notebook.widget_manager.register_widget_view('TabView', TabView);

});
