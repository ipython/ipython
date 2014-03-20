// Test keyboard invoked execution.

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

        // shift-enter
        // last cell in notebook
        var base_index = 3;
        this.select_cell(base_index);
        this.trigger_keydown('shift-enter'); // Creates one cell
        this.validate_notebook_state('shift-enter (no cell below)', 'edit', base_index + 1);
        // not last cell in notebook & starts in edit mode
        this.click_cell_editor(base_index);
        this.validate_notebook_state('click cell ' + base_index, 'edit', base_index);
        this.trigger_keydown('shift-enter');
        this.validate_notebook_state('shift-enter (cell exists below)', 'command', base_index + 1);
        // starts in command mode
        this.trigger_keydown('k');
        this.validate_notebook_state('k in comand mode', 'command', base_index);
        this.trigger_keydown('shift-enter');
        this.validate_notebook_state('shift-enter (start in command mode)', 'command', base_index + 1);

        // ctrl-enter
        // last cell in notebook
        base_index++;
        this.trigger_keydown('ctrl-enter');
        this.validate_notebook_state('ctrl-enter (no cell below)', 'command', base_index);
        // not last cell in notebook & starts in edit mode
        this.click_cell_editor(base_index-1);
        this.validate_notebook_state('click cell ' + (base_index-1), 'edit', base_index-1);
        this.trigger_keydown('ctrl-enter');
        this.validate_notebook_state('ctrl-enter (cell exists below)', 'command', base_index-1);
        // starts in command mode
        this.trigger_keydown('j');
        this.validate_notebook_state('j in comand mode', 'command', base_index);
        this.trigger_keydown('ctrl-enter');
        this.validate_notebook_state('ctrl-enter (start in command mode)', 'command', base_index);

        // alt-enter
        // last cell in notebook
        this.trigger_keydown('alt-enter'); // Creates one cell
        this.validate_notebook_state('alt-enter (no cell below)', 'edit', base_index + 1);
        // not last cell in notebook & starts in edit mode
        this.click_cell_editor(base_index);
        this.validate_notebook_state('click cell ' + base_index, 'edit', base_index);
        this.trigger_keydown('alt-enter'); // Creates one cell
        this.validate_notebook_state('alt-enter (cell exists below)', 'edit', base_index + 1);
        // starts in command mode
        this.trigger_keydown('esc', 'k');
        this.validate_notebook_state('k in comand mode', 'command', base_index);
        this.trigger_keydown('alt-enter'); // Creates one cell
        this.validate_notebook_state('alt-enter (start in command mode)', 'edit', base_index + 1);

        // Notebook will now have 8 cells, the index of the last cell will be 7.
        this.test.assertEquals(this.get_cells_length(), 8, '*-enter commands added cells where needed.');
        this.select_cell(7);
        this.validate_notebook_state('click cell ' + 7 + ' and esc', 'command', 7);
    });
});