
// Test
casper.notebook_test(function () {
    var a = 'print("a")';
    var index = this.append_cell(a);
    this.execute_cell_then(index);

    var b = 'print("b")';
    index = this.append_cell(b);
    this.execute_cell_then(index);

    var c = 'print("c")';
    index = this.append_cell(c);
    this.execute_cell_then(index);

    this.then(function () {

        // Up and down in command mode
        this.select_cell(3);
        this.trigger_keydown('j');
        this.validate_notebook_state('j at end of notebook', 'command', 3);
        this.trigger_keydown('down');
        this.validate_notebook_state('down at end of notebook', 'command', 3);
        this.trigger_keydown('up');
        this.validate_notebook_state('up', 'command', 2);
        this.select_cell(0);
        this.validate_notebook_state('select 0', 'command', 0);
        this.trigger_keydown('k');
        this.validate_notebook_state('k at top of notebook', 'command', 0);
        this.trigger_keydown('up');
        this.validate_notebook_state('up at top of notebook', 'command', 0);
        this.trigger_keydown('down');
        this.validate_notebook_state('down', 'command', 1);

        // Up and down in edit mode
        this.click_cell_editor(3);
        this.validate_notebook_state('click cell 3', 'edit', 3);
        this.trigger_keydown('down');
        this.validate_notebook_state('down at end of notebook', 'edit', 3);
        this.set_cell_editor_cursor(3, 0, 0);
        this.trigger_keydown('up');
        this.validate_notebook_state('up', 'edit', 2);
        this.click_cell_editor(0);
        this.validate_notebook_state('click 0', 'edit', 0);
        this.trigger_keydown('up');
        this.validate_notebook_state('up at top of notebook', 'edit', 0);
        this.set_cell_editor_cursor(0, 0, 10);
        this.trigger_keydown('down');
        this.validate_notebook_state('down', 'edit', 1);
    });
});
