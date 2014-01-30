//
// Test shutdown of a kernel.
//
casper.notebook_test(function () {
    // XXX: test.begin allows named sections but requires casperjs 1.1.0-DEV.
    //      We will put it back into place when the next version of casper is
    //      released. Following that, all instances of this.test can be changed
    //      to just test.
    //this.test.begin("shutdown tests (notebook)", 2, function(test) {

    // Our shutdown test closes the browser window, which will delete the
    // casper browser object, and the rest of the test suite will fail with
    // errors that look like:
    //
    //   "Error: cannot access member `evaluate' of deleted QObject"
    //
    // So what we do here is make a quick popup window, and run the test inside
    // of it.
    this.then(function() {
        this.evaluate(function(url){
            window.open(url);
        }, {url : this.getCurrentUrl()});
    })

    this.waitForPopup('');
    this.withPopup('', function () {
        this.thenEvaluate(function () {
            $('#kill_and_exit').click();
        });

        this.thenEvaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            cell.set_text('a=10; print(a)');
            cell.execute();
        });

        this.then(function () {
            var outputs = this.evaluate(function() {
                return IPython.notebook.get_cell(0).output_area.outputs;
            })
            this.test.assertEquals(outputs.length, 0, "after shutdown: no execution results");
            this.test.assertNot(this.kernel_running(),
                'after shutdown: IPython.notebook.kernel.running is false ');
        });
    });

//}); // end of test.begin
});

