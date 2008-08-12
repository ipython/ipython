# Set this prefix to where you want to install the plugin
PREFIX=~/usr/local
PREFIX=~/tmp/local

NOSE0=nosetests -vs --with-doctest --doctest-tests
NOSE=nosetests -vvs --with-ipdoctest --doctest-tests --doctest-extension=txt

#--with-color 

SRC=ipdoctest.py setup.py ../decorators.py

plugin: IPython_doctest_plugin.egg-info

dtest: plugin dtexample.py
	$(NOSE) dtexample.py

# Note: this test is double counting!!!
rtest: plugin dtexample.py
	$(NOSE) test_refs.py

std: plugin
	nosetests -vs --with-doctest --doctest-tests IPython.strdispatch
	$(NOSE) IPython.strdispatch

test: plugin dtexample.py
	$(NOSE) dtexample.py test*.py test*.txt

deb: plugin dtexample.py
	$(NOSE) test_combo.txt

iptest: plugin
	$(NOSE) IPython

deco:
	$(NOSE0) IPython.testing.decorators

mtest: plugin
	$(NOSE) -x IPython.Magic

ipipe: plugin
	$(NOSE) -x IPython.Extensions.ipipe

sr: rtest std

base: dtest rtest test std deco

all: base iptest

IPython_doctest_plugin.egg-info: $(SRC)
	python setup.py install --prefix=$(PREFIX)
	touch $@

clean:
	rm -rf IPython_doctest_plugin.egg-info *~ *pyc build/ dist/
