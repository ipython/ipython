IPython now has built-in support for progressbars::

    In[1]: from IPython.display import ProgressBar
    ...  : pb = ProgressBar(100)
    ...  : pb

    In[2]: pb.progress = 50

    # progress bar in cell 1 updates.

