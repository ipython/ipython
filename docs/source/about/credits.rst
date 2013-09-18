.. _credits:

=======
Credits
=======

IPython was started and continues to be led by Fernando Pérez.

Core developers
===============

As of this writing, core development team consists of the following
developers:

* **Fernando Pérez** <Fernando.Perez-AT-berkeley.edu> Project creator and leader, 
  IPython core, parallel computing infrastructure, testing, release manager.

* **Robert Kern** <rkern-AT-enthought.com> Co-mentored the 2005 Google Summer of
  Code project, work on IPython's core.

* **Brian Granger** <ellisonbg-AT-gmail.com> Parallel computing 
  infrastructure, IPython core, IPython notebook.

* **Benjamin (Min) Ragan-Kelley** <benjaminrk-AT-gmail.com> Parallel computing
  infrastructure, IPython core, IPython notebook.

* **Ville Vainio** <vivainio-AT-gmail.com> IPython core, maintainer of IPython
  trunk from version 0.7.2 to 0.8.4.

* **Gael Varoquaux** <gael.varoquaux-AT-normalesup.org> wxPython IPython GUI,
  frontend architecture.

* **Barry Wark** <barrywark-AT-gmail.com> Cocoa GUI, frontend architecture.

* **Laurent Dufrechou** <laurent.dufrechou-AT-gmail.com> wxPython IPython GUI.

* **Jörgen Stenarson** <jorgen.stenarson-AT-bostream.nu> Maintainer of the
  PyReadline project, which is needed for IPython under windows.

* **Thomas Kluyver** <takowl-AT-gmail.com> Port of IPython and its necessary ZeroMQ
  infrastructure to Python3, IPython core.

* **Evan Patterson** <epatters-AT-enthought.com> Qt console frontend with ZeroMQ.

* **Paul Ivanov** <pi-AT-berkeley.edu> IPython core, documentation.

* **Matthias Bussonnier** <bussonniermatthias-AT-gmail.com> IPython notebook,
  nbviewer, nbconvert.

* **Julian Taylor** <jtaylor.debian-AT-googlemail.com> IPython core, Debian packaging.

* **Brad Froehle** <brad.froehle-AT-gmail.com> IPython core.


Special thanks
==============

The IPython project is also very grateful to:

Bill Bumgarner <bbum-AT-friday.com>, for providing the DPyGetOpt module that
IPython used for parsing command line options through version 0.10.

Ka-Ping Yee <ping-AT-lfw.org>, for providing the Itpl module for convenient
and powerful string interpolation with a much nicer syntax than formatting
through the '%' operator.

Arnd Baecker <baecker-AT-physik.tu-dresden.de>, for his many very useful
suggestions and comments, and lots of help with testing and documentation
checking. Many of IPython's newer features are a result of discussions with
him.

Obviously Guido van Rossum and the whole Python development team, for creating
a great language for interactive computing.

Fernando would also like to thank Stephen Figgins <fig-AT-monitor.net>,
an O'Reilly Python editor. His October 11, 2001 article about IPP and
LazyPython, was what got this project started. You can read it at
http://www.onlamp.com/pub/a/python/2001/10/11/pythonnews.html.

Sponsors
========

We would like to thank the following entities which, at one point or another,
have provided resources and support to IPython:

* Enthought (http://www.enthought.com), for hosting IPython's website and
  supporting the project in various ways over the years, including significant
  funding and resources in 2010 for the development of our modern ZeroMQ-based
  architecture and Qt console frontend.

* Google, for supporting IPython through Summer of Code sponsorships in 2005
  and 2010.

* Microsoft Corporation, for funding in 2009 the development of documentation
  and examples of the Windows HPC Server 2008 support in IPython's parallel
  computing tools.
  
* The Nipy project (http://nipy.org) for funding in 2009 a significant
  refactoring of the entire project codebase that was key.

* Ohio Supercomputer Center ( part of Ohio State University Research
  Foundation) and the Department of Defense High Performance Computing
  Modernization Program (HPCMP), for sponsoring work in 2009 on the ipcluster
  script used for starting IPython's parallel computing processes, as well as
  the integration between IPython and the Vision environment
  (http://mgltools.scripps.edu/packages/vision).  This project would not have
  been possible without the support and leadership of Jose Unpingco, from Ohio
  State.

* Tech-X Corporation, for sponsoring a NASA SBIR project in 2008 on IPython's
  distributed array and parallel computing capabilities.

* Bivio Software (http://www.bivio.biz/bp/Intro), for hosting an IPython sprint
  in 2006 in addition to their support of the Front Range Pythoneers group in
  Boulder, CO.

  
Contributors
============

And last but not least, all the kind IPython contributors who have contributed
new code, bug reports, fixes, comments and ideas. A brief list follows, please
let us know if we have omitted your name by accident:

* Mark Voorhies <mark.voorhies-AT-ucsf.edu> Printing support in Qt console.

* Justin Riley <justin.t.riley-AT-gmail.com> Contributions to parallel support,
  Amazon EC2, Sun Grid Engine, documentation.

* Satrajit Ghosh <satra-AT-mit.edu> parallel computing (SGE and much more).

* Thomas Spura <tomspur-AT-fedoraproject.org> various fixes motivated by Fedora
  support.

* Omar Andrés Zapata Mesa <andresete.chaos-AT-gmail.com> Google Summer of Code
  2010, terminal support with ZeroMQ

* Gerardo Gutierrez <muzgash-AT-gmail.com> Google Summer of Code 2010, Qt
  notebook frontend support with ZeroMQ.

* Paul Ivanov <pivanov314-AT-gmail.com> multiline specials improvements.
  
* Dav Clark <davclark-AT-berkeley.edu> traitlets improvements.

* David Warde-Farley <wardefar-AT-iro.umontreal.ca> - bugfixes to %timeit,
  input autoindent management, and Qt console tooltips.

* Darren Dale <dsdale24-AT-gmail.com>, traits-based configuration system, Qt
  support.

* Jose Unpingco <unpingco@gmail.com> authored multiple tutorials and
  screencasts teaching the use of IPython both for interactive and parallel
  work (available in the documentation part of our website).
  
* Dan Milstein <danmil-AT-comcast.net> A bold refactor of the core prefilter
  machinery in the IPython interpreter.

* Jack Moffit <jack-AT-xiph.org> Bug fixes, including the infamous color
  problem. This bug alone caused many lost hours and frustration, many thanks
  to him for the fix. I've always been a fan of Ogg & friends, now I have one
  more reason to like these folks. Jack is also contributing with Debian
  packaging and many other things.
 
* Alexander Schmolck <a.schmolck-AT-gmx.net> Emacs work, bug reports, bug
  fixes, ideas, lots more. The ipython.el mode for (X)Emacs is Alex's code,
  providing full support for IPython under (X)Emacs.

* Andrea Riciputi <andrea.riciputi-AT-libero.it> Mac OSX information, Fink
  package management.

* Gary Bishop <gb-AT-cs.unc.edu> Bug reports, and patches to work around the
  exception handling idiosyncracies of WxPython. Readline and color support
  for Windows.

* Jeffrey Collins <Jeff.Collins-AT-vexcel.com>. Bug reports. Much improved
  readline support, including fixes for Python 2.3.

* Dryice Liu <dryice-AT-liu.com.cn> FreeBSD port.

* Mike Heeter <korora-AT-SDF.LONESTAR.ORG>

* Christopher Hart <hart-AT-caltech.edu> PDB integration.

* Milan Zamazal <pdm-AT-zamazal.org> Emacs info.

* Philip Hisley <compsys-AT-starpower.net>

* Holger Krekel <pyth-AT-devel.trillke.net> Tab completion, lots more.

* Robin Siebler <robinsiebler-AT-starband.net>

* Ralf Ahlbrink <ralf_ahlbrink-AT-web.de>

* Thorsten Kampe <thorsten-AT-thorstenkampe.de>

* Fredrik Kant <fredrik.kant-AT-front.com> Windows setup.

* Syver Enstad <syver-en-AT-online.no> Windows setup.

* Richard <rxe-AT-renre-europe.com> Global embedding.

* Hayden Callow <h.callow-AT-elec.canterbury.ac.nz> Gnuplot.py 1.6
  compatibility.
  
* Leonardo Santagada <retype-AT-terra.com.br> Fixes for Windows
  installation.
  
* Christopher Armstrong <radix-AT-twistedmatrix.com> Bugfixes.

* Francois Pinard <pinard-AT-iro.umontreal.ca> Code and
  documentation fixes.
  
* Cory Dodt <cdodt-AT-fcoe.k12.ca.us> Bug reports and Windows
  ideas. Patches for Windows installer.
  
* Olivier Aubert <oaubert-AT-bat710.univ-lyon1.fr> New magics.

* King C. Shu <kingshu-AT-myrealbox.com> Autoindent patch.

* Chris Drexler <chris-AT-ac-drexler.de> Readline packages for
  Win32/CygWin.
  
* Gustavo Cordova Avila <gcordova-AT-sismex.com> EvalDict code for
  nice, lightweight string interpolation.
  
* Kasper Souren <Kasper.Souren-AT-ircam.fr> Bug reports, ideas.

* Gever Tulley <gever-AT-helium.com> Code contributions.

* Ralf Schmitt <ralf-AT-brainbot.com> Bug reports & fixes.

* Oliver Sander <osander-AT-gmx.de> Bug reports.

* Rod Holland <rhh-AT-structurelabs.com> Bug reports and fixes to
  logging module.

* Daniel 'Dang' Griffith <pythondev-dang-AT-lazytwinacres.net>
  Fixes, enhancement suggestions for system shell use.

* Viktor Ransmayr <viktor.ransmayr-AT-t-online.de> Tests and
  reports on Windows installation issues. Contributed a true Windows
  binary installer.

* Mike Salib <msalib-AT-mit.edu> Help fixing a subtle bug related
  to traceback printing.

* W.J. van der Laan <gnufnork-AT-hetdigitalegat.nl> Bash-like
  prompt specials.

* Antoon Pardon <Antoon.Pardon-AT-rece.vub.ac.be> Critical fix for
  the multithreaded IPython.

* John Hunter <jdhunter-AT-nitace.bsd.uchicago.edu> Matplotlib
  author, helped with all the development of support for matplotlib
  in IPython, including making necessary changes to matplotlib itself.

* Matthew Arnison <maffew-AT-cat.org.au> Bug reports, '%run -d' idea.

* Prabhu Ramachandran <prabhu_r-AT-users.sourceforge.net> Help
  with (X)Emacs support, threading patches, ideas...

* Norbert Tretkowski <tretkowski-AT-inittab.de> help with Debian
  packaging and distribution.

* George Sakkis <gsakkis-AT-eden.rutgers.edu> New matcher for
  tab-completing named arguments of user-defined functions.

* Jörgen Stenarson <jorgen.stenarson-AT-bostream.nu> Wildcard
  support implementation for searching namespaces.

* Vivian De Smedt <vivian-AT-vdesmedt.com> Debugger enhancements,
  so that when pdb is activated from within IPython, coloring, tab
  completion and other features continue to work seamlessly.

* Scott Tsai <scottt958-AT-yahoo.com.tw> Support for automatic
  editor invocation on syntax errors (see
  http://www.scipy.net/roundup/ipython/issue36).

* Alexander Belchenko <bialix-AT-ukr.net> Improvements for win32
  paging system.

* Will Maier <willmaier-AT-ml1.net> Official OpenBSD port.

* Ondrej Certik <ondrej-AT-certik.cz> Set up the IPython docs to use the new
  Sphinx system used by Python, Matplotlib and many more projects.

* Stefan van der Walt <stefan-AT-sun.ac.za> Design and prototype of the
  Traits based config system.
