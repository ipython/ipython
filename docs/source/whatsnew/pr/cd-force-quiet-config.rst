OSMagics.cd_force_quiet configuration option
============================================

You can set this option to force the %cd magic to behave as if ``-q`` was passed:
::

    In [1]: cd /
    /
    
    In [2]: %config OSMagics.cd_force_quiet = True
    
    In [3]: cd /tmp
    
    In [4]:

