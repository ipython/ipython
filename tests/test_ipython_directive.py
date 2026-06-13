"""Tests for IPython.sphinxext.ipython_directive."""

import io
import os
import tempfile

import pytest

sphinx = pytest.importorskip("sphinx")
from sphinx.application import Sphinx
from IPython.sphinxext.ipython_directive import IPythonDirective


def _build_sphinx(rst_content, builder="html", tags=None):
    """Build a minimal Sphinx project, returning the count of ipython
    directives that actually executed code."""
    original_run = IPythonDirective.run
    executed = []

    def tracking_run(self):
        if not self._is_inside_excluded_only():
            executed.append(True)
        return original_run(self)

    IPythonDirective.run = tracking_run
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            srcdir = os.path.join(tmpdir, "source")
            outdir = os.path.join(tmpdir, "build")
            os.makedirs(srcdir)

            with open(os.path.join(srcdir, "conf.py"), "w") as f:
                f.write("extensions = ['IPython.sphinxext.ipython_directive']\n")

            with open(os.path.join(srcdir, "index.rst"), "w") as f:
                f.write(rst_content)

            app = Sphinx(
                srcdir,
                srcdir,
                outdir,
                os.path.join(tmpdir, "doctrees"),
                builder,
                status=io.StringIO(),
                warning=None,
            )

            if tags:
                for tag in tags:
                    app.tags.add(tag)

            app.build()
    finally:
        IPythonDirective.run = original_run

    return len(executed)


def test_only_excluded_skips_execution():
    """Code inside an excluded ``only`` block should not be executed.

    When building with the html builder, an ``only:: latex`` directive
    should cause the ipython directive to skip code execution.  See gh-9339.
    """
    n = _build_sphinx(
        """
Test
====

.. only:: latex

   .. ipython::

      In [1]: x = 1

.. ipython::

   In [1]: y = 2
""",
        builder="html",
        tags=["html"],
    )
    # The directive inside only:: latex is skipped; the one outside runs.
    assert n == 1


def test_only_included_executes_normally():
    """Code inside an included ``only`` block should execute normally.

    When building with the html builder, an ``only:: html`` directive
    should allow the ipython directive to execute code as usual.
    """
    n = _build_sphinx(
        """
Test
====

.. only:: html

   .. ipython::

      In [1]: x = 1

.. ipython::

   In [1]: y = 2
""",
        builder="html",
        tags=["html"],
    )
    # Both directives should execute.
    assert n == 2


def test_nested_only_skips_execution():
    """Nested ``only`` with a false condition should skip execution.

    When ``only:: html`` is true but the inner ``only:: latex`` is
    false, the ipython directive inside the inner block should skip.
    """
    n = _build_sphinx(
        """
Test
====

.. only:: html

   .. only:: latex

      .. ipython::

         In [1]: x = 1
""",
        builder="html",
        tags=["html"],
    )
    # The inner only:: latex is excluded, so no execution.
    assert n == 0
