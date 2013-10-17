var RadioButtonView = IPython.WidgetView.extend({
    
    // Called when view is rendered.
    render : function(){
        this.$el
            .html('')
            .addClass(this.model.comm.comm_id);
        this.update();
    },
    
    // Handles: Backend -> Frontend Sync
    //          Frontent -> Frontend Sync
    update : function(){
        
        // Add missing items to the DOM.
        var items = this.model.get('values');
        for (var index in items) {
            var item_query = ' :input[value="' + items[index] + '"]';
            if (this.$el.find(item_query).length == 0) {
                var $label = $('<label />')
                    .addClass('radio')
                    .html(items[index])
                    .appendTo(this.$el);
                
                var that = this;
                $('<input />')
                    .attr('type', 'radio')
                    .addClass(this.model)
                    .val(items[index])
                    .prependTo($label)
                    .on('click', function(e){
                        that.model.set('value', $(e.target).val(), this);
                        that.model.apply();
                    });
            }
            
            if (this.model.get('value') == items[index]) {
                this.$el.find(item_query).prop('checked', true);
            } else {
                this.$el.find(item_query).prop('checked', false);
            }
        }
        
        // Remove items that no longer exist.
        this.$el.find('input').each(function(i, obj) {
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
    },
    
});

IPython.notebook.widget_manager.register_widget_view('RadioButtonView', RadioButtonView);
