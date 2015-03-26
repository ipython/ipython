IPython Documentation
---------------------

This directory contains the majority of the documentation for IPython. 

Deploy docs
-----------

Run ``make gh-pages``, and follow instruction, that is to say:
cd into ``gh-pages``, check that everything is alright and push.



Requirements
------------
The following tools are needed to build the documentation:

sphinx jsdoc

On Debian-based systems, you should be able to run::

    sudo apt-get install python-sphinx npm
    sudo npm install -g jsdoc@"<=3.3.0"

The documentation gets built using ``make``, and comes in several flavors.

``make html`` - build the API (both Javascript and Python) and narrative 
documentation web pages, this is the the default ``make`` target, so 
running just ``make`` is equivalent to ``make html``. 

``make html_noapi`` - same as above, but without running the auto-generated
API docs. When you are working on the narrative documentation, the most time
consuming portion  of the build process is the processing and rending of the
API documentation. This build target skips that.

``make jsapi`` - build Javascript auto-generated API documents.

``make pdf`` will compile a pdf from the documentation.

You can run ``make help`` to see information on all possible make targets.



