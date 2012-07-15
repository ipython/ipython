# Simple makefile to rapidly deploy IPython with all its dependencies.

# Configuration section.  The version numbers and paths declared here may
# change with each release.

# IPython version
IPYTHON_VER=0.9.1

# Declare here version numbers of all the dependencies
PYOPENSSL_VER=0.6
ZOPE_INTERFACE_VER=3.4.1
TWISTED_VER=8.1.0
FOOLSCAP_VER=0.3.1
NOSE_VER=0.10.3

# Repository URLs for all packages.  Make sure these are correct for each
# release, since projects may change paths!
IPYTHON_REPO=http://ipython.scipy.org/dist
PYOPENSSL_REPO=http://downloads.sourceforge.net/pyopenssl
ZOPE_INTERFACE_REPO=http://pypi.python.org/packages/source/z/zope.interface
TWISTED_REPO=http://tmrc.mit.edu/mirror/twisted/Twisted/8.1
FOOLSCAP_REPO=http://foolscap.lothar.com/releases
NOSE_REPO=http://somethingaboutorange.com/mrl/projects/nose

#-----------------------------------------------------------------------------
# Main code begins.  There shouldn't be much to change here with each release.
#

# Hand-written files to ship in self-contained tarball
SOURCES=pkginstall pkginstall.cfg Makefile README.txt README.html

# Versions of tarballs we ship
IPYTHON=ipython-$(IPYTHON_VER).tar.gz
IP_ALLDEPS=ipython-alldeps-$(IPYTHON_VER)

PYOPENSSL=pyOpenSSL-$(PYOPENSSL_VER).tar.gz
ZOPE_INTERFACE=zope.interface-$(ZOPE_INTERFACE_VER).tar.gz
NOSE=nose-$(NOSE_VER).tar.gz
TWISTED=Twisted-$(TWISTED_VER).tar.bz2
FOOLSCAP=foolscap-$(FOOLSCAP_VER).tar.gz

TARBALLS=$(PYOPENSSL) $(ZOPE_INTERFACE) $(TWISTED) $(FOOLSCAP) \
$(NOSE) $(IPYTHON)

# URLs for downloads

#-----------------------------------------------------------------------------
# Target declaration
#

# Targets to install, in correct dependency order
install: pyopenssl zope.interface twisted foolscap nose ipython
	echo
	echo "IPython Installation finished."
	echo "You can now run the ipython test suite by running:"
	echo "iptest"
	echo "If all tests pass, you can delete this entire directory."
	echo

# Download targets
download: $(TARBALLS)

$(IPYTHON):
	wget $(IPYTHON_REPO)/$(IPYTHON)

$(PYOPENSSL):
	wget $(PYOPENSSL_REPO)/$(PYOPENSSL)

$(ZOPE_INTERFACE):
	wget $(ZOPE_INTERFACE_REPO)/$(ZOPE_INTERFACE)

$(TWISTED):
	wget $(TWISTED_REPO)/$(TWISTED)

$(FOOLSCAP):
	wget $(FOOLSCAP_REPO)/$(FOOLSCAP)

$(NOSE):
	wget $(NOSE_REPO)/$(NOSE)


# The calls to pkginstall must use the actual Python package name
nose: $(NOSE)
	./pkginstall nose

zope.interface: $(ZOPE_INTERFACE)
	./pkginstall zope.interface zope

pyopenssl: $(PYOPENSSL)
	./pkginstall pyOpenSSL OpenSSL

twisted: $(TWISTED)
	./pkginstall Twisted

foolscap: $(FOOLSCAP)
	./pkginstall foolscap

ipython: $(IPYTHON)
	./pkginstall ipython IPython

# Distribution targets
dist: $(IP_ALLDEPS).tar

$(IP_ALLDEPS).tar: download readme
	-mkdir $(IP_ALLDEPS)
	-ln $(SOURCES) $(TARBALLS) $(IP_ALLDEPS)/
	tar cf $(IP_ALLDEPS).tar $(IP_ALLDEPS)
	rm -rf $(IP_ALLDEPS)

readme: README.html

README.html: README.txt
	rst2html README.txt > README.html

# Auxiliary targets
upload: dist
	rsync -e ssh -av README.html $(IP_ALLDEPS).tar \
	ipython@ipython.scipy.org:www/dist/alldeps

clean:
	ls -p | grep /$ | xargs rm -rf
	rm -f $(IP_ALLDEPS)* *~

distclean: clean
	rm -f $(TARBALLS)
	rm README.html

info:
	echo "TARBALLS"
	echo $(TARBALLS)
