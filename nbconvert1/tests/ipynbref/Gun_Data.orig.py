## Some gun violence analysis with Wikipedia data

# As [requested by John Stokes](https://twitter.com/jonst0kes/status/282330530412888064),
# here are per-capita numbers for gun-related homicides,
# relating to GDP and total homicides,
# so the situation in the United States can be put in context relative to other nations.

# main data source is UNODC (via Wikipedia [here](http://en.wikipedia.org/wiki/List_of_countries_by_intentional_homicide_rate)
# and [here](http://en.wikipedia.org/wiki/List_of_countries_by_firearm-related_death_rate)).
# 
# GDP data from World Bank, again [via Wikipedia](http://en.wikipedia.org/wiki/List_of_countries_by_GDP_(PPP)_per_capita).
# 
# If the numbers on Wikipedia are inaccurate, or their relationship is not sound
# (e.g. numbers taken from different years, during which significant change occured)
# then obviously None of this analysis is valid.
# 
# To summarize the data,
# every possible way you look at it the US is lousy at preventing gun violence.
# Even when compared to significantly more violent places,
# gun violence in the US is a serious problem,
# and when compared to similarly wealthy places,
# the US is an outstanding disaster.

# **UPDATE:** the relationship of the gun data and totals does not seem to be valid.
# [FBI data](http://www2.fbi.gov/ucr/cius2009/offenses/violent_crime/index.html) suggests that
# the relative contribution of guns to homicides in the US is 47%,
# but relating these two data sources gives 80%.
# Internal comparisons should still be fine, but 'fraction' analysis has been stricken.

# In[1]:
%load_ext retina
%pylab inline

# Out[1]:
#     
#     Welcome to pylab, a matplotlib-based Python environment [backend: module://IPython.zmq.pylab.backend_inline].
#     For more information, type 'help(pylab)'.
# 
# In[2]:
from IPython.display import display
import pandas
pandas.set_option('display.notebook_repr_html', True)
pandas.set_option('display.precision', 2)

# Some utility functions for display

# In[3]:
def plot_percent(df, limit=10):
    df['Gun Percent'][:limit].plot()
    plt.ylim(0,100)
    plt.title("% Gun Homicide")
    plt.show()


# In[4]:
def plot_percapita(df, limit=10):
    df = df.ix[:,['Homicides', 'Gun Homicides']][:limit]
    df['Total Homicides'] = df['Homicides'] - df['Gun Homicides']
    del df['Homicides']
    df.plot(kind='bar', stacked=True, sort_columns=True)
    plt.ylabel("per 100k")
    plt.show()


# In[8]:
def display_relevant(df, limit=10):
    display(df.ix[:,['Homicides', 'Gun Homicides', 'Gun Data Source']][:limit])

# Load the data

# In[9]:
totals = pandas.read_csv('totals.csv', '\t', index_col=0)
guns = pandas.read_csv('guns.csv', '\t', index_col=0)
gdp = pandas.read_csv('gdp.csv', '\t', index_col=1)
data = totals.join(guns).join(gdp)
data['Gun Percent'] = 100 * data['Gun Homicides'] / data['Homicides']
del data['Unintentional'],data['Undetermined'],data['Gun Suicides']
data = data.dropna()

# Of all sampled countries (Found data for 68 countries),
# the US is in the top 15 in Gun Homicides per capita.
# 
# Numbers are per 100k.

# In[10]:
data = data.sort("Gun Homicides", ascending=False)
display_relevant(data, 15)

# Out[10]:
#                    Homicides  Gun Homicides Gun Data Source
#     Country                                                
#     El Salvador         69.2           50.4     OAS 2011[1]
#     Jamaica             52.2           47.4     OAS 2011[1]
#     Honduras            91.6           46.7     OAS 2011[1]
#     Guatemala           38.5           38.5     OAS 2011[1]
#     Colombia            33.4           27.1  UNODC 2011 [2]
#     Brazil              21.0           18.1   UNODC 2011[3]
#     Panama              21.6           12.9     OAS 2011[1]
#     Mexico              16.9           10.0   UNODC 2011[4]
#     Paraguay            11.5            7.3  UNODC 2000[11]
#     Nicaragua           13.6            7.1     OAS 2011[1]
#     United States        4.2            3.7  OAS 2012[5][6]
#     Costa Rica          10.0            3.3   UNODC 2002[7]
#     Uruguay              5.9            3.2   UNODC 2002[7]
#     Argentina            3.4            3.0  UNODC 2011[12]
#     Barbados            11.3            3.0  UNODC 2000[11]
# Take top 30 Countries by GDP

# In[11]:
top = data.sort('GDP')[-30:]

# and rank them by Gun Homicides per capita:

# In[12]:
top_by_guns = top.sort("Gun Homicides", ascending=False)
display_relevant(top_by_guns, 5)
plot_percapita(top_by_guns, 10)

# Out[12]:
#                    Homicides  Gun Homicides Gun Data Source
#     Country                                                
#     United States        4.2            3.7  OAS 2012[5][6]
#     Israel               2.1            0.9    WHO 2012[10]
#     Canada               1.6            0.8   Krug 1998[13]
#     Luxembourg           2.5            0.6    WHO 2012[10]
#     Greece               1.5            0.6   Krug 1998[13]
# image file: tests/ipynbref/Gun_Data_orig_files/Gun_Data_orig_fig_00.png

# **NOTE:** these bar graphs should not be interpreted as fractions of a total,
# as the two data sources do not appear to be comparable.
# But the red and blue bar graphs should still be internally comparable.

# The US is easily #1 of 30 wealthiest countries in Gun Homicides per capita,
# by a factor of 4:1

# Adding USA, Canada, and Mexico to all of Europe,
# USA is a strong #2 behind Mexico in total gun homicides per-capita

# In[13]:
index = (data['Region'] == 'Europe') + \
        (data.index == 'United States') + \
        (data.index == 'Canada') + \
        (data.index == 'Mexico')
selected = data[index]

print "By Total Gun Homicides"
sys.stdout.flush()

by_guns = selected.sort("Gun Homicides", ascending=False)
#by_guns['Gun Homicides'].plot(kind='bar')
plot_percapita(by_guns, limit=25)
display_relevant(selected, limit=None)


# Out[13]:
#     By Total Gun Homicides
# 
# image file: tests/ipynbref/Gun_Data_orig_files/Gun_Data_orig_fig_01.png

#                     Homicides  Gun Homicides Gun Data Source
#     Country                                                 
#     Mexico               16.9           10.0   UNODC 2011[4]
#     United States         4.2            3.7  OAS 2012[5][6]
#     Montenegro            3.5            2.1    WHO 2012[10]
#     Moldova               7.5            1.0    WHO 2012[10]
#     Canada                1.6            0.8   Krug 1998[13]
#     Serbia                1.2            0.6    WHO 2012[10]
#     Luxembourg            2.5            0.6    WHO 2012[10]
#     Greece                1.5            0.6   Krug 1998[13]
#     Croatia               1.4            0.6    WHO 2012[10]
#     Switzerland           0.7            0.5     OAS 2011[1]
#     Malta                 1.0            0.5    WHO 2012[10]
#     Portugal              1.2            0.5    WHO 2012[10]
#     Belarus               4.9            0.4   UNODC 2002[7]
#     Ireland               1.2            0.4    WHO 2012[10]
#     Italy                 0.9            0.4    WHO 2012[10]
#     Ukraine               5.2            0.3  UNODC 2000[11]
#     Estonia               5.2            0.3    WHO 2012[10]
#     Belgium               1.7            0.3    WHO 2012[10]
#     Finland               2.2            0.3    WHO 2012[10]
#     Lithuania             6.6            0.2    WHO 2012[10]
#     Bulgaria              2.0            0.2    WHO 2012[10]
#     Georgia               4.3            0.2    WHO 2012[10]
#     Denmark               0.9            0.2    WHO 2012[10]
#     France                1.1            0.2    WHO 2012[10]
#     Netherlands           1.1            0.2    WHO 2012[10]
#     Sweden                1.0            0.2    WHO 2012[10]
#     Slovakia              1.5            0.2    WHO 2012[10]
#     Austria               0.6            0.2    WHO 2012[10]
#     Latvia                3.1            0.2    WHO 2012[10]
#     Spain                 0.8            0.1    WHO 2012[10]
#     Hungary               1.3            0.1    WHO 2012[10]
#     Czech Republic        1.7            0.1    WHO 2012[10]
#     Germany               0.8            0.1    WHO 2012[10]
#     Slovenia              0.7            0.1    WHO 2012[10]
#     Romania               2.0            0.0    WHO 2012[10]
#     United Kingdom        1.2            0.0    WHO2012 [10]
#     Norway                0.6            0.0    WHO 2012[10]
#     Poland                1.1            0.0    WHO 2012[10]
# Let's just compare US, Canada, and UK:

# In[15]:
select = data.ix[['United States', 'Canada', 'United Kingdom']]
plot_percapita(select)

# Out[15]:
# image file: tests/ipynbref/Gun_Data_orig_files/Gun_Data_orig_fig_02.png

# Normalize to the US numbers (inverse)

# In[16]:
select['Homicides'] = select['Homicides']['United States'] / select['Homicides']
select['Gun Homicides'] = select['Gun Homicides']['United States'] / select['Gun Homicides']
display_relevant(select)

# Out[16]:
#                     Homicides  Gun Homicides Gun Data Source
#     United States         1.0            1.0  OAS 2012[5][6]
#     Canada                2.6            4.9   Krug 1998[13]
#     United Kingdom        3.5           92.5    WHO2012 [10]
# So, you are 2.6 times more likely to be killed in the US than Canada,
# and 3.5 times more likely than in the UK.
# That's bad, but not extreme.
# 
# However, you are 4.9 times more likely to be killed *with a gun* in the US than Canada,
# and almost 100 times more likely than in the UK.  That is pretty extreme.
# 

# Countries represented:

# In[14]:
for country in data.index:
    print country

# Out[14]:
#     El Salvador
#     Jamaica
#     Honduras
#     Guatemala
#     Colombia
#     Brazil
#     Panama
#     Mexico
#     Paraguay
#     Nicaragua
#     United States
#     Costa Rica
#     Uruguay
#     Argentina
#     Barbados
#     Montenegro
#     Peru
#     Moldova
#     Israel
#     India
#     Canada
#     Serbia
#     Luxembourg
#     Greece
#     Uzbekistan
#     Croatia
#     Kyrgyzstan
#     Switzerland
#     Malta
#     Portugal
#     Belarus
#     Ireland
#     Italy
#     Kuwait
#     Ukraine
#     Estonia
#     Belgium
#     Finland
#     Lithuania
#     Cyprus
#     Bulgaria
#     Georgia
#     Denmark
#     France
#     Netherlands
#     Sweden
#     Slovakia
#     Qatar
#     Austria
#     Latvia
#     New Zealand
#     Spain
#     Hungary
#     Czech Republic
#     Hong Kong
#     Australia
#     Singapore
#     Chile
#     Germany
#     Slovenia
#     Romania
#     Azerbaijan
#     South Korea
#     United Kingdom
#     Norway
#     Japan
#     Poland
#     Mauritius
# 