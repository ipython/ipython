Regression tests for the web notebook. These tests depend on
[CasperJS](http://casperjs.org/), which in turn requires
a recent version of [PhantomJS](http://phantomjs.org/).

Run the tests:

```sh
/path/to/bin/casperjs test --includes=util.js test_cases
```

The file `util.js` contains utility functions for tests,
including a hardcoded path to a running notebook server
(http://127.0.0.1:8888 by default).
