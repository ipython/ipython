## Opening an Issue

When opening a new Issue, please take the following steps:

1. Search GitHub and/or Google for your issue to avoid duplicate reports.
   Keyword searches for your error messages are most helpful.
2. If possible, try updating to master and reproducing your issue,
   because we may have already fixed it.
3. Try to include a minimal reproducible test case
4. Include relevant system information.  Start with the output of:

        python -c "import IPython; print(IPython.sys_info())"

   And include any relevant package versions, depending on the issue,
   such as matplotlib, numpy, Qt, Qt bindings (PyQt/PySide), tornado, web browser, etc.

## Pull Requests

Some guidelines on contributing to IPython:

* All work is submitted via Pull Requests.
* Pull Requests can be submitted as soon as there is code worth discussing.
  Pull Requests track the branch, so you can continue to work after the PR is submitted.
  Review and discussion can begin well before the work is complete,
  and the more discussion the better.
  The worst case is that the PR is closed.
* Pull Requests should generally be made against master
* Pull Requests should be tested, if feasible:
    - bugfixes should include regression tests
    - new behavior should at least get minimal exercise

[Travis](http://travis-ci.org/#!/ipython/ipython) does a pretty good job testing IPython and Pull Requests,
but it may make sense to manually perform tests (possibly with our `test_pr` script),
particularly for PRs that affect `IPython.parallel` or Windows.

For more detailed information, see our [GitHub Workflow](https://github.com/ipython/ipython/wiki/Dev:-GitHub-workflow).

