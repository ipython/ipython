var DropdownView = IPython.WidgetView.extend({
    
    // Called when view is rendered.
    render : function(){
        
        this.$el
            .html('')
            .addClass(this.model.comm.comm_id);
        this.$buttongroup = $('<div />')
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
    },
    
});

IPython.notebook.widget_manager.register_widget_view('DropdownView', DropdownView);
