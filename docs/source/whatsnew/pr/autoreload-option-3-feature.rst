Autoreload 3 feature
====================

Example: When an IPython session is ran with the 'autoreload' extension loaded,
you will now have the option '3' to select which means the following:

    1. replicate all functionality from option 2
    2. autoload all new funcs/classes/enums/globals from the module when they're added
    3. autoload all newly imported funcs/classes/enums/globals from external modules

Try ``%autoreload 3`` in an IPython session after running ``%load_ext autoreload``

For more information please see unit test - 
    extensions/tests/test_autoreload.py : 'test_autoload_newly_added_objects'
