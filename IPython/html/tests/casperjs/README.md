# IPython Notebook Javascript Tests

Regression tests for the web notebook. These tests depend on
[CasperJS](http://casperjs.org/), which in turn requires
a recent version of [PhantomJS](http://phantomjs.org/).

Run the tests using:

```
iptest js
```

For finer granularity, or to specify more options, you can also run the
following `casperjs` command

```sh
/path/to/bin/casperjs test --includes=util.js test_cases
```

The file `util.js` contains utility functions for tests, including a path to a
running notebook server on localhost (http://127.0.0.1) with the port number
specified as a command line argument to the test suite. Port 8888 is used if
`--port=` is not specified.
