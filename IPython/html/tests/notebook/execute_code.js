//
// Test code cell execution.
//
casper.notebook_test(function () {
    this.evaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        cell.set_text('a=10; print(a)');
        cell.execute();
    });

    this.wait_for_output(0);

    // refactor this into  just a get_output(0)
    this.then(function () {
        var result = this.get_output_cell(0);
        this.test.assertEquals(result.text, '10\n', 'cell execute (using js)');
    });


    // do it again with the keyboard shortcut
    this.thenEvaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        cell.set_text('a=11; print(a)');
        cell.clear_output();
    });

    this.then(function(){
        
        this.trigger_keydown('shift-enter');
    });

    this.wait_for_output(0);

    this.then(function () {
        var result = this.get_output_cell(0);
        var num_cells = this.get_cells_length();
        this.test.assertEquals(result.text, '11\n', 'cell execute (using ctrl-enter)');
        this.test.assertEquals(num_cells, 2, 'shift-enter adds a new cell at the bottom')
    });
    
    // do it again with the keyboard shortcut
    this.thenEvaluate(function () {
        IPython.notebook.select(1);
        IPython.notebook.delete_cell();
        var cell = IPython.notebook.get_cell(0);
        cell.set_text('a=12; print(a)');
        cell.clear_output();
    });

    this.then(function(){
        this.trigger_keydown('ctrl-enter');
    });

    this.wait_for_output(0);

    this.then(function () {
        var result = this.get_output_cell(0);
        var num_cells = this.get_cells_length();
        this.test.assertEquals(result.text, '12\n', 'cell execute (using shift-enter)');
        this.test.assertEquals(num_cells, 1, 'ctrl-enter adds no new cell at the bottom')
    });

    // press the "play" triangle button in the toolbar
    this.thenEvaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        IPython.notebook.select(0);
        cell.clear_output();
        cell.set_text('a=13; print(a)');
        $('#run_b').click();
    });
    
    this.wait_for_output(0);

    this.then(function () {
        var result = this.get_output_cell(0);
        this.test.assertEquals(result.text, '13\n', 'cell execute (using "play" toolbar button)')
    });
});
