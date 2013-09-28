//
// Test code cell execution.
//
casper.notebook_test(function () {
    this.evaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        cell.set_text('a=10; print a');
        cell.execute();
    });


    this.waitFor(function () {
        return this.evaluate(function get_output() {
            var cell = IPython.notebook.get_cell(0);
            return cell.output_area.outputs.length != 0;
        })
    }, null, function on_timeout() {
            this.echo( this.evaluate( function() {
                IPython.notebook.save_notebook();
                return IPython.notebook.notebook_name;
            }) + ".ipynb is the name of the notebook which failed");
    });

    this.then(function () {
        var result = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var output = cell.output_area.outputs[0].text;
            return output;
        })
        this.test.assertEquals(result, '10\n', 'stdout output matches')
    });
});
