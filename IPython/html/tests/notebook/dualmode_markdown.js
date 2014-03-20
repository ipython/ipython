
// Test
casper.notebook_test(function () {
    var a = 'print("a")';
    var index = this.append_cell(a);
    this.execute_cell_then(index);

    this.then(function () {
        // Markdown rendering / unredering
        this.select_cell(1);
        this.validate_notebook_state('select 1', 'command', 1);
        this.trigger_keydown('m');
        this.test.assertEquals(this.get_cell(1).cell_type, 'markdown', 'm; cell is markdown');
        this.test.assertEquals(this.get_cell(1).rendered, false, 'm; cell is rendered');
        this.trigger_keydown('enter');
        this.test.assertEquals(this.get_cell(1).rendered, false, 'enter; cell is unrendered');
        this.validate_notebook_state('enter', 'edit', 1);
        this.trigger_keydown('ctrl-enter');
        this.test.assertEquals(this.get_cell(1).rendered, true, 'ctrl-enter; cell is rendered');
        this.validate_notebook_state('enter', 'command', 1);
        this.trigger_keydown('enter');
        this.test.assertEquals(this.get_cell(1).rendered, false, 'enter; cell is unrendered');
        this.select_cell(0);
        this.test.assertEquals(this.get_cell(1).rendered, false, 'select 0; cell 1 is still unrendered');
        this.validate_notebook_state('select 0', 'command', 0);
        this.select_cell(1);
        this.validate_notebook_state('select 1', 'command', 1);
        this.trigger_keydown('ctrl-enter');
        this.test.assertEquals(this.get_cell(1).rendered, true, 'ctrl-enter; cell is rendered');
        this.select_cell(0);
        this.validate_notebook_state('select 0', 'command', 0);
        this.trigger_keydown('shift-enter');
        this.validate_notebook_state('shift-enter', 'command', 1);
        this.test.assertEquals(this.get_cell(1).rendered, true, 'shift-enter; cell is rendered');
        this.trigger_keydown('shift-enter'); // Creates one cell
        this.validate_notebook_state('shift-enter', 'edit', 2);
        this.test.assertEquals(this.get_cell(1).rendered, true, 'shift-enter; cell is rendered');
    });
});