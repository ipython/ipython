
//
// Tests for the Session object
//

casper.notebook_test(function () {
    var that = this;
    var get_info = function () {
        return that.evaluate(function () {
            return JSON.parse(JSON.stringify(IPython.notebook.session._get_model()));
        });
    };

    // test that the kernel is running
    this.then(function () {
        this.test.assert(this.kernel_running(), 'session: kernel is running');
    });

    // test list
    this.thenEvaluate(function () {
        IPython._sessions = null;
        IPython.notebook.session.list(function (data) {
            IPython._sessions = data;
        });
    });
    this.waitFor(function () {
        return this.evaluate(function () {
            return IPython._sessions !== null;
        });
    });
    this.then(function () {
        var num_sessions = this.evaluate(function () {
            return IPython._sessions.length;
        });
        this.test.assertEquals(num_sessions, 1, 'one session running');
    });

    // test get_info
    var session_info = get_info();
    this.thenEvaluate(function () {
        IPython._session_info = null;
        IPython.notebook.session.get_info(function (data) {
            IPython._session_info = data;
        });
    });
    this.waitFor(function () {
        return this.evaluate(function () {
            return IPython._session_info !== null;
        });
    });
    this.then(function () {
        var new_session_info = this.evaluate(function () {
            return IPython._session_info;
        });
        this.test.assertEquals(session_info.notebook.name, new_session_info.notebook.name, 'session: notebook name correct');
        this.test.assertEquals(session_info.notebook.path, new_session_info.notebook.path, 'session: notebook path correct');
        this.test.assertEquals(session_info.kernel.name, new_session_info.kernel.name, 'session: kernel name correct');
        this.test.assertEquals(session_info.kernel.id, new_session_info.kernel.id, 'session: kernel id correct');
    });

    // test rename_notebook
    //
    // TODO: the PATCH request isn't supported by phantom, so this test always
    // fails, see https://github.com/ariya/phantomjs/issues/11384
    // when this is fixed we can properly run this test
    //
    // this.thenEvaluate(function () {
    //     IPython._renamed = false;
    //     IPython.notebook.session.rename_notebook(
    //         "foo",
    //         "bar",
    //         function (data) {
    //             IPython._renamed = true;
    //         }
    //     );
    // });
    // this.waitFor(function () {
    //     return this.evaluate(function () {
    //         return IPython._renamed;
    //     });
    // });
    // this.then(function () {
    //     var info = get_info();
    //     this.test.assertEquals(info.notebook.name, "foo", "notebook was renamed");
    //     this.test.assertEquals(info.notebook.path, "bar", "notebook path was changed");
    // });

    // test delete
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

    // check for events when starting the session
    this.event_test(
        'start_session',
        [
            'kernel_started.Session',
            'status_connected.Kernel',
            // technically we should get this message, but sometimes the kernel
            // finishes starting before we connect to it so then we don't receive
            // this message
            //
            //'status_starting.Kernel',
            'status_busy.Kernel',
            'status_idle.Kernel'
        ],
        function () {
            this.thenEvaluate(function () {
                IPython.notebook.session.start();
            });
        }
    );
    this.wait(500);

    // check for events when killing the session
    this.event_test(
        'delete_session',
        ['status_killed.Session'],
        function () {
            this.thenEvaluate(function () {
                IPython.notebook.session.delete();
            });
        }
    );
    this.wait(500);

    // check for events when restarting the session
    this.event_test(
        'restart_session',
        [
            'status_killed.Session',
            'kernel_started.Session',
            'status_connected.Kernel',
            // technically we should get this message, but sometimes the kernel
            // finishes starting before we connect to it so then we don't receive
            // this message
            //
            //'status_starting.Kernel',
            'status_busy.Kernel',
            'status_idle.Kernel'
        ],
        function () {
            this.thenEvaluate(function () {
                IPython.notebook.session.restart();
            });
        }
    );
    this.wait(500);

    // check for events when starting a nonexistant kernel
    this.event_test(
        'bad_start_session',
        [
            'status_killed.Session',
            'kernel_dead.Session'
        ],
        function () {
            this.thenEvaluate(function () {
                IPython.notebook.session.restart({kernel_name: 'foo'});
            });
        }
    );
});
