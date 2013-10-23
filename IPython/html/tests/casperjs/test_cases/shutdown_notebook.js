//
// Test shutdown of a kernel.
//
casper.notebook_test(function () {
    this.test.begin("shutdown tests (notebook)", 2, function(test) {

    casper.thenEvaluate(function () {
        $('#kill_and_exit').click();
    });
    
    casper.thenEvaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        cell.set_text('a=10; print(a)');
        cell.execute();
    });

    // refactor this into  just a get_output(0)
    casper.then(function () {
        var result = this.get_output_cell(0);
        test.assertFalsy(result, "after shutdown: no execution results");
        test.assertNot(this.kernel_running(), 
            'after shutdown: IPython.notebook.kernel.running is false ');
    });

});
});

