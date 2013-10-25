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
});