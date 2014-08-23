
//
// Kernel tests
//
casper.notebook_test(function () {
    this.evaluate(function () {
        IPython.notebook.kernel.kernel_info(
            function(msg){
                IPython._kernel_info_response = msg;
            })
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
        var kernel = IPython.notebook.session.kernel;
        IPython._channels = [
            kernel.shell_channel,
            kernel.iopub_channel,
            kernel.stdin_channel
        ];
        kernel.kill();
    });
    
    this.waitFor(function () {
        return this.evaluate(function(){
            for (var i=0; i < IPython._channels.length; i++) {
                var ws = IPython._channels[i];
                if (ws.readyState !== ws.CLOSED) {
                    return false;
                }
            }
            return true;
        });
    });
    
    this.then(function () {
        var states = this.evaluate(function() {
            var states = [];
            for (var i = 0; i < IPython._channels.length; i++) {
                states.push(IPython._channels[i].readyState);
            }
            return states;
        });
        
        for (var i = 0; i < states.length; i++) {
            this.test.assertEquals(states[i], WebSocket.CLOSED,
                "Kernel.kill closes websockets[" + i + "]");
        }
    });
});
