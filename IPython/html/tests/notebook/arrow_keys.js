//
// Check for errors with up and down arrow presses in a non-empty notebook.
//
casper.notebook_test(function () {
    var result = this.evaluate(function() {
        IPython.notebook.command_mode();
        pos0 = IPython.notebook.get_selected_index();
        IPython.keyboard.trigger_keydown('b');
        pos1 = IPython.notebook.get_selected_index();
        IPython.keyboard.trigger_keydown('b');
        pos2 = IPython.notebook.get_selected_index();
        // Simulate the "up arrow" and "down arrow" keys.
        IPython.keyboard.trigger_keydown('up');
        pos3 = IPython.notebook.get_selected_index();
        IPython.keyboard.trigger_keydown('down');
        pos4 = IPython.notebook.get_selected_index();
        return  pos0 == 0 &&
                pos1 == 1 &&
                pos2 == 2 &&
                pos3 == 1 &&
                pos4 == 2;
    });
    this.test.assertTrue(result, 'Up/down arrow okay in non-empty notebook.');
});
