## Opening an Issue

When opening a new Issue, please take the following steps:

1. Search GitHub and/or Google for your issue to avoid duplicate reports.
   Keyword searches for your error messages are most helpful.
2. If possible, try updating to main and reproducing your issue,
   because we may have already fixed it.
3. Try to include a minimal reproducible test case.
4. Include relevant system information.  Start with the output of:

        python -c "import IPython; print(IPython.sys_info())"

   And include any relevant package versions, depending on the issue, such as
   matplotlib, numpy, Qt, Qt bindings (PyQt/PySide), tornado, web browser, etc.

## Triaging issue and Fixing issue

**Do NOT leave a message asking if you can work on an issue; start by trying to
reproduce it and fix it**

You are looking for an issue to fix and find an issue that can be close or you
suspect is not relevant anymore, please comment on it and say so to avoid future
contributor to lose time doing the same.

If you have technical questions or reproducing question you are allowed to:

 - Ask clarification on the issue.
 - Open a draft PR even with terrible code and ask for advice.

## Pull Requests

Some guidelines on contributing to IPython:

* All work is submitted via Pull Requests.
* Pull Requests can be submitted as soon as there is code worth discussing.
  Pull Requests track the branch, so you can continue to work after the PR is submitted.
  Review and discussion can begin well before the work is complete,
  and the more discussion the better.
  The worst case is that the PR is closed.
* Pull Requests should generally be made against main
* Pull Requests should be tested, if feasible:
    - bugfixes should include regression tests.
    - new behavior should at least get minimal exercise.
* New features and backwards-incompatible changes should be documented by adding
  a new file to the [pr](docs/source/whatsnew/pr) directory, see [the README.md
  there](docs/source/whatsnew/pr/README.md) for details.
* Don't make 'cleanup' pull requests just to change code style.
  We don't follow any style guide strictly, and we consider formatting changes
  unnecessary noise.
  If you're making functional changes, you can clean up the specific pieces of
  code you're working on.

[GitHub Actions](https://github.com/ipython/ipython/actions/workflows/test.yml) does
a pretty good job testing IPython and Pull Requests,
but it may make sense to manually perform tests,
particularly for PRs that affect `IPython.parallel` or Windows.

For more detailed information, see our [GitHub Workflow](https://github.com/ipython/ipython/wiki/Dev:-GitHub-workflow).

## Running Tests

All the tests can be run by using
```shell
pytest
```

All the tests for a single module (for example **test_alias**) can be run by using the fully qualified path to the module.
```shell
pytest IPython/core/tests/test_alias.py
```

Only a single test (for example **test_alias_lifecycle**) within a single file can be run by adding the specific test after a `::` at the end:
```shell
pytest IPython/core/tests/test_alias.py::test_alias_lifecycle
```

## Documentation

Sphinx documentation can be built locally using standard sphinx `make` commands. To build HTML documentation from the root of the project, execute:

```shell
pip install -r docs/requirements.txt   # only needed once
make -C docs/ html SPHINXOPTS="-W"
```

To force update of the API documentation, precede the `make` command with:

```shell
python3 docs/autogen_api.py
```

Similarly, to force-update the configuration, run:

```shell
python3 docs/autogen_config.py
```
