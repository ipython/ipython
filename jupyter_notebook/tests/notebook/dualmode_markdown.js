
// Test
casper.notebook_test(function () {
    var a = 'print("a")';
    var index = this.append_cell(a);
    this.execute_cell_then(index, function(index) {
        // Markdown rendering / unredering
        this.select_cell(index);
        this.validate_notebook_state('select ' + index, 'command', index);
        this.trigger_keydown('m');
        this.test.assertEquals(this.get_cell(index).cell_type, 'markdown', 'm; cell is markdown');
        this.test.assert(!this.is_cell_rendered(index), 'm; cell is unrendered');
        this.trigger_keydown('enter');
        this.test.assert(!this.is_cell_rendered(index), 'enter; cell is unrendered');
        this.validate_notebook_state('enter', 'edit', index);
        this.trigger_keydown('ctrl-enter');
        this.test.assert(this.is_cell_rendered(index), 'ctrl-enter; cell is rendered');
        this.validate_notebook_state('enter', 'command', index);
        this.trigger_keydown('enter');
        this.test.assert(!this.is_cell_rendered(index), 'enter; cell is unrendered');
        this.select_cell(index-1);
        this.test.assert(!this.is_cell_rendered(index), 'select ' + (index-1) + '; cell ' + index + ' is still unrendered');
        this.validate_notebook_state('select ' + (index-1), 'command', index-1);
        this.select_cell(index);
        this.validate_notebook_state('select ' + index, 'command', index);
        this.trigger_keydown('ctrl-enter');
        this.test.assert(this.is_cell_rendered(index), 'ctrl-enter; cell is rendered');
        this.select_cell(index-1);
        this.validate_notebook_state('select ' + (index-1), 'command', index-1);
        this.trigger_keydown('shift-enter');
        this.validate_notebook_state('shift-enter', 'command', index);
        this.test.assert(this.is_cell_rendered(index), 'shift-enter; cell is rendered');
        this.trigger_keydown('shift-enter'); // Creates one cell
        this.validate_notebook_state('shift-enter', 'edit', index+1);
        this.test.assert(this.is_cell_rendered(index), 'shift-enter; cell is rendered');
    });
});