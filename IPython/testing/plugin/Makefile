# Set this prefix to where you want to install the plugin
PREFIX=~/usr/local
PREFIX=~/tmp/local

plugin: IPython_doctest_plugin.egg-info

test: plugin dtexample.py
	nosetests -s --with-ipdoctest --doctest-tests --doctest-extension=txt \
	dtexample.py test*.txt

deb: plugin dtexample.py
	nosetests -vs --with-ipdoctest --doctest-tests --doctest-extension=txt \
        test_combo.txt

iptest: plugin
	nosetests -vs --with-ipdoctest --doctest-tests --doctest-extension=txt \
        IPython

IPython_doctest_plugin.egg-info: ipdoctest.py setup.py
	python setup.py install --prefix=$(PREFIX)
	touch $@

clean:
	rm -rf IPython_doctest_plugin.egg-info *~ *pyc build/ dist/
