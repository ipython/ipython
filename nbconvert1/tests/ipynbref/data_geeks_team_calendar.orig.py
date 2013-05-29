# In[1]:
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

# In[2]:
target = "mikedewar"
line_draw_target(target)
        

# Out[2]:
# image file: tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_00.png

# In[3]:
target = "drewconway"
line_draw_target(target)

# Out[3]:
# image file: tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_01.png

# In[4]:
target = "hmason"
line_draw_target(target)

# Out[4]:
# image file: tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_02.png

# In[5]:
target = "mbostock"
line_draw_target(target)

# Out[5]:
# image file: tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_03.png

# In[6]:
target = "amueller"
line_draw_target(target)

# Out[6]:
# image file: tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_04.png

