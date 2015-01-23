.. _nbformat:

===========================
The Jupyter Notebook Format
===========================

Introduction
============

Jupyter (né IPython) notebook files are simple JSON documents,
containing text, source code, rich media output, and metadata.
each segment of the document is stored in a cell.

Some general points about the notebook format:

.. note::

    *All* metadata fields are optional.
    While the type and values of some metadata are defined,
    no metadata values are required to be defined.


Top-level structure
===================

At the highest level, a Jupyter notebook is a dictionary with a few keys:

- metadata (dict)
- nbformat (int)
- nbformat_minor (int)
- cells (list)

.. sourcecode:: python

    {
      "metadata" : {
        "signature": "hex-digest", # used for authenticating unsafe outputs on load
        "kernel_info": {
            # if kernel_info is defined, its name field is required.
            "name" : "the name of the kernel"
        },
        "language_info": {
            # if language_info is defined, its name field is required.
            "name" : "the programming language of the kernel",
            "version": "the version of the language",
            "codemirror_mode": "The name of the codemirror mode to use [optional]"
        }
      },
      "nbformat": 4,
      "nbformat_minor": 0,
      "cells" : [
          # list of cell dictionaries, see below
      ],
    }

Some fields, such as code input and text output, are characteristically multi-line strings.
When these fields are written to disk, they **may** be written as a list of strings,
which should be joined with ``''`` when reading back into memory.
In programmatic APIs for working with notebooks (Python, Javascript),
these are always re-joined into the original multi-line string.
If you intend to work with notebook files directly,
you must allow multi-line string fields to be either a string or list of strings.


Cell Types
==========

There are a few basic cell types for encapsulating code and text.
All cells have the following basic structure:

.. sourcecode:: python

    {
      "cell_type" : "name",
      "metadata" : {},
      "source" : "single string or [list, of, strings]",
    }


Markdown cells
--------------

Markdown cells are used for body-text, and contain markdown,
as defined in `GitHub-flavored markdown`_, and implemented in marked_.

.. _GitHub-flavored markdown: https://help.github.com/articles/github-flavored-markdown
.. _marked: https://github.com/chjj/marked

.. sourcecode:: python

    {
      "cell_type" : "markdown",
      "metadata" : {},
      "source" : ["some *markdown*"],
    }

.. versionchanged:: nbformat 4.0

    Heading cells have been removed, in favor of simple headings in markdown.


Code cells
----------

Code cells are the primary content of Jupyter notebooks.
They contain source code in the language of the document's associated kernel,
and a list of outputs associated with executing that code.
They also have an execution_count, which must be an integer or ``null``.

.. sourcecode:: python

    {
      "cell_type" : "code",
      "execution_count": 1, # integer or null
      "metadata" : {
          "collapsed" : True, # whether the output of the cell is collapsed
          "autoscroll": False, # any of true, false or "auto"
      },
      "source" : ["some code"],
      "outputs": [{
          # list of output dicts (described below)
          "output_type": "stream",
          ...
      }],
    }

.. versionchanged:: nbformat 4.0

    ``input`` was renamed to ``source``, for consistency among cell types.

.. versionchanged:: nbformat 4.0

    ``prompt_number`` renamed to ``execution_count``

Code cell outputs
-----------------

A code cell can have a variety of outputs (stream data or rich mime-type output).
These correspond to :ref:`messages <messaging>` produced as a result of executing the cell.

All outputs have an ``output_type`` field,
which is a string defining what type of output it is.


stream output
*************

.. sourcecode:: python

    {
      "output_type" : "stream",
      "name" : "stdout", # or stderr
      "text" : ["multiline stream text"],
    }

.. versionchanged:: nbformat 4.0

    The keys ``stream`` key was changed to ``name`` to match
    the stream message.


display_data
************

Rich display outputs, as created by ``display_data`` messages,
contain data keyed by mime-type. This is often called a mime-bundle,
and shows up in various locations in the notebook format and message spec.
The metadata of these messages may be keyed by mime-type as well.



.. sourcecode:: python

    {
      "output_type" : "display_data",
      "data" : {
        "text/plain" : ["multiline text data"],
        "image/png": ["base64-encoded-png-data"],
        "application/json": {
          # JSON data is included as-is
          "json": "data",
        },
      },
      "metadata" : {
        "image/png": {
          "width": 640,
          "height": 480,
        },
      },
    }


.. versionchanged:: nbformat 4.0

    ``application/json`` output is no longer double-serialized into a string.

.. versionchanged:: nbformat 4.0

    mime-types are used for keys, instead of a combination of short names (``text``)
    and mime-types, and are stored in a ``data`` key, rather than the top-level.
    i.e. ``output.data['image/png']`` instead of ``output.png``.


execute_result
**************

Results of executing a cell (as created by ``displayhook`` in Python)
are stored in ``execute_result`` outputs.
`execute_result` outputs are identical to ``display_data``,
adding only a ``execution_count`` field, which must be an integer.

.. sourcecode:: python

    {
      "output_type" : "execute_result",
      "execution_count": 42,
      "data" : {
        "text/plain" : ["multiline text data"],
        "image/png": ["base64-encoded-png-data"],
        "application/json": {
          # JSON data is included as-is
          "json": "data",
        },
      },
      "metadata" : {
        "image/png": {
          "width": 640,
          "height": 480,
        },
      },
    }

.. versionchanged:: nbformat 4.0

    ``pyout`` renamed to ``execute_result``

.. versionchanged:: nbformat 4.0

    ``prompt_number`` renamed to ``execution_count``


error
*****

Failed execution may show a traceback

.. sourcecode:: python

    {
      'ename' : str,   # Exception name, as a string
      'evalue' : str,  # Exception value, as a string

      # The traceback will contain a list of frames,
      # represented each as a string.
      'traceback' : list,
    }

.. versionchanged:: nbformat 4.0

    ``pyerr`` renamed to ``error``


.. _raw nbconvert cells:

Raw NBConvert cells
-------------------

A raw cell is defined as content that should be included *unmodified* in :ref:`nbconvert <nbconvert>` output.
For example, this cell could include raw LaTeX for nbconvert to pdf via latex,
or restructured text for use in Sphinx documentation.

The notebook authoring environment does not render raw cells.

The only logic in a raw cell is the `format` metadata field.
If defined, it specifies which nbconvert output format is the intended target
for the raw cell. When outputting to any other format,
the raw cell's contents will be excluded.
In the default case when this value is undefined,
a raw cell's contents will be included in any nbconvert output,
regardless of format.

.. sourcecode:: python

    {
      "cell_type" : "raw",
      "metadata" : {
        # the mime-type of the target nbconvert format.
        # nbconvert to formats other than this will exclude this cell.
        "format" : "mime/type"
      },
      "source" : ["some nbformat mime-type data"]
    }

Metadata
========

Metadata is a place that you can put arbitrary JSONable information about
your notebook, cell, or output. Because it is a shared namespace,
any custom metadata should use a sufficiently unique namespace,
such as `metadata.kaylees_md.foo = "bar"`.

Metadata fields officially defined for Jupyter notebooks are listed here:

Notebook metadata
-----------------

The following metadata keys are defined at the notebook level:

=========== =============== ==============
Key         Value           Interpretation
=========== =============== ==============
kernelspec  dict            A :ref:`kernel specification <kernelspecs>`
signature   str             A hashed :ref:`signature <notebook_security>` of the notebook
=========== =============== ==============


Cell metadata
-------------

The following metadata keys are defined at the cell level:

=========== =============== ==============
Key         Value           Interpretation
=========== =============== ==============
collapsed   bool            Whether the cell's output container should be collapsed
autoscroll  bool or 'auto'  Whether the cell's output is scrolled, unscrolled, or autoscrolled
deletable   bool            If False, prevent deletion of the cell
format      'mime/type'     The mime-type of a :ref:`Raw NBConvert Cell <raw nbconvert cells>`
name        str             A name for the cell. Should be unique
tags        list of str     A list of string tags on the cell. Commas are not allowed in a tag
=========== =============== ==============

Output metadata
---------------

The following metadata keys are defined for code cell outputs:

=========== =============== ==============
Key         Value           Interpretation
=========== =============== ==============
isolated    bool            Whether the output should be isolated into an IFrame
=========== =============== ==============
