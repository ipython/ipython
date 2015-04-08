//
// Test merging two notebook cells.
//
casper.notebook_test(function() {
    var that = this;
    var set_cells_text =  function () {
        that.evaluate(function() {
            var cell_one = IPython.notebook.get_selected_cell();
            cell_one.set_text('a = 5');
        });

        that.trigger_keydown('b');

        that.evaluate(function() {
            var cell_two = IPython.notebook.get_selected_cell();
            cell_two.set_text('print(a)');
        });
    };

    this.evaluate(function () {
        IPython.notebook.command_mode();
    });
        
    // merge_cell_above()
    set_cells_text();
    var output_above = this.evaluate(function () {
        IPython.notebook.merge_cell_above();
        return IPython.notebook.get_selected_cell().get_text();
    });
        
    // merge_cell_below()
    set_cells_text();
    var output_below = this.evaluate(function() {
        IPython.notebook.select(0);
        IPython.notebook.merge_cell_below();
        return IPython.notebook.get_selected_cell().get_text();
    });
    
    this.test.assertEquals(output_above, 'a = 5\nprint(a)',
                           'Successful merge_cell_above().');
    this.test.assertEquals(output_below, 'a = 5\nprint(a)',
                           'Successful merge_cell_below().');
});
