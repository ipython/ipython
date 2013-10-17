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

    this.then(function () {
        var result = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var output = cell.output_area.outputs[0].text;
            return output;
        })
        this.test.assertEquals(result, '10\n', 'cell execute (using js)')
    });


    // do it again with the keyboard shortcut
    this.thenEvaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        cell.set_text('a=11; print(a)');
        cell.clear_output()
        IPython.utils.press_ctrl_enter();
    });

    this.wait_for_output(0);

    this.then(function () {
        var result = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var output = cell.output_area.outputs[0].text;
            return output;
        })
        this.test.assertEquals(result, '11\n', 'cell execute (using ctrl-enter)')
    });
    
    // do it again with the keyboard shortcut
    this.thenEvaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        cell.set_text('a=12; print(a)');
        cell.clear_output()
        IPython.utils.press_shift_enter();
    });

    this.wait_for_output(0);

    this.then(function () {
        var result = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var output = cell.output_area.outputs[0].text;
            return output;
        })
        this.test.assertEquals(result, '12\n', 'cell execute (using shift-enter)')
    });
});
