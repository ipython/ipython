"""
An IPython extension that provides a magic command that displays
a table with information about versions of installed modules.

This makes it much easier to determine which versions of modules
were installed in the source IPython interpreter's environment.

Produces output in:

* Plaintext (IPython [qt]console)
* HTML (IPython notebook, ``nbconvert --to html``, ``--to slides``)
* JSON (IPython notebook ``.ipynb`` files)
* LaTeX (e.g. ``ipython nbconvert example.ipynb --to LaTeX --post PDF``)

Usage
======

.. sourcecode:: ipython

   In [1]: %load_ext version_information

   In [2]: %version_information
   Out[2]:
   Software versions
   Python 2.7.3 (default, Sep 26 2013, 20:08:41) [GCC 4.6.3]
   IPython 2.0.0-dev
   OS posix [linux2]

   Mon Dec 09 10:21:40 2013 CST

   In [3]: %version_information sphinx, jinja2
   Out[3]:
   Software versions
   Python 2.7.3 (default, Sep 26 2013, 20:08:41) [GCC 4.6.3]
   IPython 2.0.0-dev
   OS posix [linux2]
   sphinx 1.2b3
   jinja2 2.7.1

   Mon Dec 09 10:21:52 2013 CST

.. note:: ``%version_information`` expects to find the module version in
   ``<module>.__version__``.

   If ``<module>.__version__`` is not set, it attempts to get a version
   string with ``pkg_resources.require('<module>')[0].version``
   (the ``version`` field from ``setup.py``).

"""
import cgi
import json
import os
import sys
import time

import IPython
from IPython.core.magic import magics_class, line_magic, Magics

try:
    import pkg_resources
except ImportError:
    pkg_resources = None

@magics_class
class VersionInformation(Magics):

    @line_magic
    def version_information(self, line=''):
        """Show information about versions of modules.

        Usage:

            %version_information [optional comma-separated list of modules]

        """
        self.packages = [("Python", sys.version.replace("\n", "")),
                         ("IPython", IPython.__version__),
                         ("OS", "%s [%s]" % (os.name, sys.platform))]

        modules = line.replace(' ', '').split(",")

        for module in modules:
            if len(module) > 0:
                try:
                    code = "import %s; version=%s.__version__" % (module, module)
                    ns_g = ns_l = {}
                    exec(compile(code, "<string>", "exec"), ns_g, ns_l)
                    self.packages.append((module, ns_l["version"]))
                except Exception as e:
                    try:
                        if pkg_resources is None:
                            raise
                        version = pkg_resources.require(module)[0].version
                        self.packages.append((module, version))
                    except Exception as e:
                        self.packages.append((module, str(e)))

        return self


    def _repr_json_(self):
        obj = {
            'Software versions': [
                {'module': name, 'version': version} for
                (name, version) in self.packages]}
        return json.dumps(obj)


    def _repr_html_(self):

        html = "<table>"
        html += "<tr><th>Software</th><th>Version</th></tr>"
        for name, version in self.packages:
            _version = cgi.escape(version)
            html += "<tr><td>%s</td><td>%s</td></tr>" % (name, _version)

        html += "<tr><td colspan='2'>%s</td></tr>" % \
                    time.strftime('%a %b %d %H:%M:%S %Y %Z')
        html += "</table>"

        return html


    @staticmethod
    def _latex_escape(str_):
        CHARS = {
            '&':  r'\&',
            '%':  r'\%',
            '$':  r'\$',
            '#':  r'\#',
            '_':  r'\letterunderscore{}',
            '{':  r'\letteropenbrace{}',
            '}':  r'\letterclosebrace{}',
            '~':  r'\lettertilde{}',
            '^':  r'\letterhat{}',
            '\\': r'\letterbackslash{}',
            '>':  r'\textgreater',
            '<':  r'\textless',
        }
        return u"".join([CHARS.get(c, c) for c in str_])


    def _repr_latex_(self):

        latex = r"\begin{tabular}{|l|l|}\hline" + "\n"
        latex += r"{\bf Software} & {\bf Version} \\ \hline\hline" + "\n"
        for name, version in self.packages:
            _version = self._latex_escape(version)
            latex += r"%s & %s \\ \hline" % (name, _version) + "\n"

        latex += r"\hline \multicolumn{2}{|l|}{%s} \\ \hline" % \
                    time.strftime('%a %b %d %H:%M:%S %Y %Z') + "\n"
        latex += r"\end{tabular}" + "\n"

        return latex


    def _repr_pretty_(self, pp, cycle):

        text = "Software versions\n"
        for name, version in self.packages:
            text += "%s %s\n" % (name, version)

        text += "\n%s" % time.strftime('%a %b %d %H:%M:%S %Y %Z')

        pp.text(text)


def load_ipython_extension(ipython):
    ipython.register_magics(VersionInformation)
