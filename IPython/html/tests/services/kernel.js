
//
// Kernel tests
//
casper.notebook_test(function () {
    this.then(function () {
        this.test.assert(this.kernel_running(), 'kernel: kernel is running');
    });

    this.evaluate(function () {
        IPython.notebook.kernel.kernel_info(
            function(msg){
                IPython._kernel_info_response = msg;
            });
    });

    this.waitFor(
        function () {
            return this.evaluate(function(){
                return IPython._kernel_info_response;
        });
    });

    this.then(function () {
        var kernel_info_response =  this.evaluate(function(){
            return IPython._kernel_info_response;
        });
        this.test.assertTrue( kernel_info_response.msg_type === 'kernel_info_reply', 'Kernel info request return kernel_info_reply');
        this.test.assertTrue( kernel_info_response.content !== undefined, 'Kernel_info_reply is not undefined');
    });
    
    this.thenEvaluate(function () {
        IPython.notebook.kernel.kill();
    });
    
    this.waitFor(function () {
        return this.evaluate(function () {
            return IPython.notebook.kernel.is_fully_disconnected();
        });
    });
    
    this.then(function () {
        this.test.assert(!this.kernel_running(), 'kernel is not running');
    });
});
