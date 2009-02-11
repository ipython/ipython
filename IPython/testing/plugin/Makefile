# Set this prefix to where you want to install the plugin
PREFIX=/usr/local

NOSE0=nosetests -vs --with-doctest --doctest-tests --detailed-errors
NOSE=nosetests -vvs --with-ipdoctest --doctest-tests --doctest-extension=txt \
--detailed-errors

SRC=ipdoctest.py setup.py ../decorators.py

# Default target for clean 'make'
default: iplib

# The actual plugin installation
plugin: IPython_doctest_plugin.egg-info

# Simple targets that test one thing
simple: plugin simple.py
	$(NOSE) simple.py

dtest: plugin dtexample.py
	$(NOSE) dtexample.py

rtest: plugin test_refs.py
	$(NOSE) test_refs.py

test: plugin dtexample.py
	$(NOSE) dtexample.py test*.py test*.txt

deb: plugin dtexample.py
	$(NOSE) test_combo.txt

# IPython tests
deco:
	$(NOSE0) IPython.testing.decorators

magic: plugin
	$(NOSE) IPython.Magic

ipipe: plugin
	$(NOSE) IPython.Extensions.ipipe

iplib: plugin
	$(NOSE)  IPython.iplib

strd: plugin
	$(NOSE) IPython.strdispatch

engine: plugin
	$(NOSE) IPython.kernel

tf: plugin
	$(NOSE) IPython.config.traitlets

# All of ipython itself
ipython: plugin
	$(NOSE) IPython


# Combined targets
sr: rtest strd

base: dtest rtest test strd deco

quick: base iplib ipipe

all: base ipython

# Main plugin and cleanup
IPython_doctest_plugin.egg-info: $(SRC)
	python setup.py install --prefix=$(PREFIX)
	touch $@

clean:
	rm -rf IPython_doctest_plugin.egg-info *~ *pyc build/ dist/
