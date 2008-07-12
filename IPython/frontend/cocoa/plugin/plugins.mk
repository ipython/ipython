%.plugin::
	rm -rf dist/$(notdir $@)
	rm -rf build dist && \
	python setup.py py2app -s

%.py:
	@echo "test -f $@"
	@test -f %@

%.nib:
	@echo "test -f $@"
	@test -f %@

.DEFAULT_GOAL := all

.PHONY : all clean

clean :
	rm -rf build dist


