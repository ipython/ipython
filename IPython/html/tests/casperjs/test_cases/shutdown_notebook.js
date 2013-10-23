//
// Test shutdown of a kernel.
//
casper.notebook_test(function () {
    // XXX: test.begin allows named sections but requires casperjs 1.1.0-DEV.
    //      We will put it back into place when the next version of casper is
    //      released. Following that, all instances of this.test can be changed
    //      to just test.
    //this.test.begin("shutdown tests (notebook)", 2, function(test) {

    this.thenEvaluate(function () {
        $('#kill_and_exit').click();
    });
    
    this.thenEvaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        cell.set_text('a=10; print(a)');
        cell.execute();
    });

    // refactor this into  just a get_output(0)
    this.then(function () {
        var result = this.get_output_cell(0);
        this.test.assertFalsy(result, "after shutdown: no execution results");
        this.test.assertNot(this.kernel_running(), 
            'after shutdown: IPython.notebook.kernel.running is false ');
    });

//}); // end of test.begin
});

