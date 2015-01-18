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
        $("button[data-jupyter-action='ipython.run-select-next']")[0].click()
    });
    
    this.wait_for_output(0);

    this.then(function () {
        var result = this.get_output_cell(0);
        this.test.assertEquals(result.text, '13\n', 'cell execute (using "play" toolbar button)')
    });

    // run code with skip_exception
    this.thenEvaluate(function () {
        var cell0 = IPython.notebook.get_cell(0);
        cell0.set_text('raise IOError');
        IPython.notebook.insert_cell_below('code',0);
        var cell1 = IPython.notebook.get_cell(1);
        cell1.set_text('a=14; print(a)');
        cell0.execute(false);
        cell1.execute();
    });

    this.wait_for_output(1);

    this.then(function () {
        var result = this.get_output_cell(1);
        this.test.assertEquals(result.text, '14\n', "cell execute, don't stop on error");
    });

    this.thenEvaluate(function () {
        var cell0 = IPython.notebook.get_cell(0);
        cell0.set_text('raise IOError');
        IPython.notebook.insert_cell_below('code',0);
        var cell1 = IPython.notebook.get_cell(1);
        cell1.set_text('a=14; print(a)');
        cell0.execute();
        cell1.execute();
    });

    this.wait_for_output(0);

    this.then(function () {
        var outputs = this.evaluate(function() {
            return IPython.notebook.get_cell(1).output_area.outputs;
        })
        this.test.assertEquals(outputs.length, 0, 'cell execute, stop on error (default)');
    });
});
