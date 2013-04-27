In[1]:

.. code:: python

    #! /usr/bin/env python
    '''
    github_team_calendar.py
    Python program to scrape friends github to build team calendar for github
    '''
    
    
    import json
    import requests
    import pandas as pd
    
    
    def line_draw_target(target):                                                    
        github_url = 'https://github.com/users/%s/contributions_calendar_data'       
        r = requests.get(github_url % target)                                                                                                                                                                                                                                                                                   
        data = json.loads(r.text)                                                    
        dates, contributions = zip(*data)                                            
        ts = pd.Series(contributions, index=dates)
        plt.plot(ts)

In[2]:

.. code:: python

    target = "mikedewar"
    line_draw_target(target)
            

.. image:: tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_00.png

In[3]:

.. code:: python

    target = "drewconway"
    line_draw_target(target)

.. image:: tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_01.png

In[4]:

.. code:: python

    target = "hmason"
    line_draw_target(target)

.. image:: tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_02.png

In[5]:

.. code:: python

    target = "mbostock"
    line_draw_target(target)

.. image:: tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_03.png

In[6]:

.. code:: python

    target = "amueller"
    line_draw_target(target)

.. image:: tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_04.png

