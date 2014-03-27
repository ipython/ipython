
// Test
casper.notebook_test(function () {
    this.then(function () {
        // Split and merge cells
        this.select_cell(0);
        this.trigger_keydown('a', 'enter'); // Create cell above and enter edit mode.
        this.validate_notebook_state('a, enter', 'edit', 0);
        this.set_cell_text(0, 'abcd');
        this.set_cell_editor_cursor(0, 0, 2);
        this.test.assertEquals(this.get_cell_text(0), 'abcd', 'Verify that cell 0 has the new contents.');
        this.trigger_keydown('ctrl-shift-subtract'); // Split
        this.test.assertEquals(this.get_cell_text(0), 'ab', 'split; Verify that cell 0 has the first half.');
        this.test.assertEquals(this.get_cell_text(1), 'cd', 'split; Verify that cell 1 has the second half.');
        this.validate_notebook_state('split', 'edit', 1);
        this.select_cell(0); // Move up to cell 0
        this.trigger_keydown('shift-m'); // Merge
        this.validate_notebook_state('merge', 'command', 0);
        this.test.assertEquals(this.get_cell_text(0), 'ab\ncd', 'merge; Verify that cell 0 has the merged contents.');
    });
});