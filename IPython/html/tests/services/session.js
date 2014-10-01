
//
// Tests for the Session object
//

casper.notebook_test(function () {
    this.then(function () {
        this.test.assert(this.kernel_running(), 'session: kernel is running');
    });

    this.thenEvaluate(function () {
        IPython.notebook.session.delete();
    });

    this.waitFor(function () {
        return this.evaluate(function () {
            return IPython.notebook.kernel.is_fully_disconnected();
        });
    });

    this.then(function () {
        this.test.assert(!this.kernel_running(), 'session deletes kernel');
    });
});
