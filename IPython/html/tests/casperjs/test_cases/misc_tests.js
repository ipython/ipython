
//
// Miscellaneous javascript tests
//
casper.notebook_test(function () {
    var jsver = this.evaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        cell.set_text('import IPython; print(IPython.__version__)');
        cell.execute();
        return IPython.version;
    });

    this.wait_for_output(0);

    // refactor this into  just a get_output(0)
    this.then(function () {
        var result = this.get_output_cell(0);
        this.test.assertEquals(result.text.trim(), jsver, 'IPython.version in JS matches IPython.');
    });

});
