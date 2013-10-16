//
// Test kernel interrupt 
//
casper.notebook_test(function () {
    this.evaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        cell.set_text('import time\nfor x in range(3):\n    time.sleep(1)');
        cell.execute();
    });

    this.thenClick('li#int_kernel');

    this.waitFor(function () {
        return this.evaluate(function get_output() {
            var cell = IPython.notebook.get_cell(0);
            return cell.output_area.outputs.length != 0;
        })
    });

    this.then(function () {
        var result = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var output = cell.output_area.outputs[0].ename;
            return output;
        })
        this.test.assertEquals(result, 'KeyboardInterrupt', 'keyboard interrupt')
    });
});
