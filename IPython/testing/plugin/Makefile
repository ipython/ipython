# Set this prefix to where you want to install the plugin
PREFIX=/usr/local

NOSE0=nosetests -vs --with-doctest --doctest-tests --detailed-errors
NOSE=nosetests -vvs --with-ipdoctest --doctest-tests --doctest-extension=txt \
--detailed-errors

SRC=ipdoctest.py setup.py ../decorators.py

# Default target for clean 'make'
default: interactiveshell

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
	$(NOSE) IPython.core.magic

excolors: plugin
	$(NOSE) IPython.core.excolors

interactiveshell: plugin
	$(NOSE)  IPython.core.interactiveshell

strd: plugin
	$(NOSE) IPython.core.strdispatch

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

quick: base interactiveshell ipipe

all: base ipython

# Main plugin and cleanup
IPython_doctest_plugin.egg-info: $(SRC)
	python setup.py install --prefix=$(PREFIX)
	touch $@

clean:
	rm -rf IPython_doctest_plugin.egg-info *~ *pyc build/ dist/
