"""Embed IPython using the simple embed function rather than the class API."""

from IPython import embed

a = 10
b = 20

embed(header='First time', banner1='')

c = 30
d = 40

try:
    raise Exception('adsfasdf')
except:
    embed(header='The second time')
