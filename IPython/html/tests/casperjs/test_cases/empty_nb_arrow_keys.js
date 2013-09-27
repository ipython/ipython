//
// Check for errors with up and down arrow presses in an empty notebook.
//
casper.notebook_test(function () {
    var result = this.evaluate(function() {
        var ncells = IPython.notebook.ncells(),
            i;
        
        // Delete all cells.
        for (i = 0; i < ncells; i++) {
            IPython.notebook.delete_cell();
        }
        
        // Simulate the "up arrow" and "down arrow" keys.
        var up_press = $.Event('keydown', {which: $.ui.keyCode.UP});
        $(document).trigger(up_press);
        var down_press = $.Event('keydown', {which: $.ui.keyCode.DOWN});
        $(document).trigger(down_press);
        return true;
    });
    this.test.assertTrue(result, 'Up/down arrow okay in empty notebook.');
});
