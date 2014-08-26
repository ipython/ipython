
//
// Tests for the Session object
//

casper.notebook_test(function () {
    this.evaluate(function () {
        var kernel = IPython.notebook.session.kernel;
        IPython._channels = [
            kernel.shell_channel,
            kernel.iopub_channel,
            kernel.stdin_channel
        ];
        IPython.notebook.session.delete();
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
                "Session.delete closes websockets[" + i + "]");
        }
    });
});
