require(["../static/notebook/js/widget"], function(){
    var SelectionWidgetModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('SelectionWidgetModel', SelectionWidgetModel);

    var DropdownView = IPython.WidgetView.extend({
        
        // Called when view is rendered.
        render : function(){
            
            this.$el
                .html('');
            this.$buttongroup = $('<div />')
                                .addClass('widget_item')
                                .addClass('btn-group')
                                .appendTo(this.$el);
            this.$droplabel = $('<button />')
                                .addClass('btn')
                                .appendTo(this.$buttongroup);
            this.$dropbutton = $('<button />')
                                .addClass('btn')
                                .addClass('dropdown-toggle')
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
            this.$droplabel.html(this.model.get('value'));
            
            var items = this.model.get('values');
            this.$droplist.html('');
            for (var index in items) {
                var that = this;
                var item_button = $('<a href="#"/>')
                    .html(items[index])
                    .on('click', function(e){
                        that.model.set('value', $(e.target).html(), this );
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
            return IPython.WidgetView.prototype.update.call(this);
        },
        
    });

    IPython.notebook.widget_manager.register_widget_view('DropdownView', DropdownView);

    var RadioButtonsView = IPython.WidgetView.extend({
        
        // Called when view is rendered.
        render : function(){
            this.$el
                .html('');
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
                            that.model.update_other_views(that);
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
            return IPython.WidgetView.prototype.update.call(this);
        },
        
    });

    IPython.notebook.widget_manager.register_widget_view('RadioButtonsView', RadioButtonsView);


    var ToggleButtonsView = IPython.WidgetView.extend({
        
        // Called when view is rendered.
        render : function(){
            this.$el
                .html('');
            this.$buttongroup = $('<div />')
                .addClass('btn-group')
                .attr('data-toggle', 'buttons-radio')
                .appendTo(this.$el);
            this.update();
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            
            // Add missing items to the DOM.
            var items = this.model.get('values');
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
                
                if (this.model.get('value') == items[index]) {
                    this.$buttongroup.find(item_query).addClass('active');
                } else {
                    this.$buttongroup.find(item_query).removeClass('active');
                }
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
            return IPython.WidgetView.prototype.update.call(this);
        },
        
    });

    IPython.notebook.widget_manager.register_widget_view('ToggleButtonsView', ToggleButtonsView);
});
