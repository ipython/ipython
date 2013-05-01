"""Exporter for the notebook conversion pipeline.

This module defines Exporter, a highly configurable converter
that uses Jinja2 to export notebook files into different format.

You can register both pre-transformers that will act on the notebook format
befor conversion and jinja filter that would then be availlable in the templates
"""

#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function, absolute_import

# Stdlib imports
import io
import os

# IPython imports
from IPython.config.configurable import Configurable
from IPython.nbformat import current as nbformat
from IPython.utils.traitlets import MetaHasTraits, Unicode, List, Bool
from IPython.utils.text import indent

# other libs/dependencies
from jinja2 import Environment, FileSystemLoader
from markdown import markdown

# local import
import filters.strings
import filters.markdown
import filters.latex
import filters.datatypefilter
import filters.pygments
import filters.ansi

import transformers.extractfigure
import transformers.csshtmlheader
import transformers.revealhelp
import transformers.coalescestreams


#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

#Standard Jinja2 environment constants
TEMPLATE_PATH = "/../templates/"
TEMPLATE_SKELETON_PATH = "/../templates/skeleton/"
TEMPLATE_EXTENSION = ".tpl"

#Jinja2 extensions to load.
JINJA_EXTENSIONS = ['jinja2.ext.loopcontrols']

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------
class Exporter(Configurable):
    """ A Jinja2 base converter templates

    Pre-process the IPYNB files, feed it through Jinja2 templates,
    and spit an converted files and a data object with other data
    should be mostly configurable
    """

    pre_transformer_order = List(['haspyout_transformer'],
        config=True,
        help= """
            An ordered list of pre-transformer to apply to the IPYNB
            file before running through templates
            """
        )

    template_file = Unicode(
            '', config=True,
            help="Name of the template file to use")

    fileext = Unicode(
        'txt', config=True, 
        help="Extension of the file that should be written to disk"
        )

    stdout = Bool(
        True, config=True,
        help="""Whether to print the converted IPYNB file to stdout
        "use full do diff files without actually writing a new file"""
        )

    write = Bool(
        False, config=True,
        help="""Should the converted notebook file be written to disk
        along with potential extracted resources."""
        )

    #Processors that process the input data prior to the export, set in the 
    #constructor for this class.
    preprocessors = [] 

    def __init__(self, preprocessors={}, jinja_filters={}, config=None, export_format, **kw):
        """ Init a new converter.

        config: the Configurable config object to pass around.

        preprocessors: dict of **availlable** key/value function to run on
                       ipynb json data before conversion to extract/inline file.
                       See `transformer.py` and `ConfigurableTransformers`

                       set the order in which the transformers should apply
                       with the `pre_transformer_order` trait of this class

                       transformers registerd by this key will take precedence on
                       default one.

        jinja_filters: dict of supplementary jinja filter that should be made
                       availlable in template. If those are of Configurable Class type,
                       they will be instanciated with the config object as argument.

                       user defined filter will overwrite the one availlable by default.
        """

        #Set the default options for the exporter.
        default_config = self.config
            
        #Set properties that must be set in the config class in order to 
        #propagate to other classes.
        default_config.GlobalConfigurable.display_data_priority =['svg', 'png', 'latex', 'jpg', 'jpeg','text']
        default_config.ExtractFigureTransformer.display_data_priority=['svg', 'png', 'latex', 'jpg', 'jpeg','text']

        #Set default properties of the exporter.
        #For most (or all cases), the template file name matches the format name.
        self.display_data_priority= ['svg', 'png', 'latex', 'jpg', 'jpeg','text']
        self.template_file = export_format

        if not config == None:
            default_config._merge(config)
        config = default_config    
    
        #Call the base class constructor
        super(Exporter, self).__init__(config=config, **kw)

        #Standard environment
        self.ext = TEMPLATE_EXTENSION
        self._init_environment()

        #TODO: Implement reflection style methods to get user transformers.        
        #for name in self.pre_transformer_order:
        #    # get the user-defined transformer first
        #    transformer = preprocessors.get(name, getattr(trans, name, None))
        #    if isinstance(transformer, MetaHasTraits):
        #        transformer = transformer(config=config)
        #    self.preprocessors.append(transformer)

        #For compatibility, TODO: remove later.
        self.preprocessors.append(transformers.coalescestreams.coalesce_streams)
        self.preprocessors.append(transformers.extractfigure.ExtractFigureTransformer(config=config))
        self.preprocessors.append(transformers.revealhelp.RevealHelpTransformer(config=config))
        self.preprocessors.append(transformers.csshtmlheader.CSSHtmlHeaderTransformer(config=config))

        #Add filters to the Jinja2 environment
        self._register_filters(config)

        #Load user filters.  Overwrite existing filters if need be.
        for key, user_filter in jinja_filters.iteritems():
            if isinstance(user_filter, MetaHasTraits):
                self.env.filters[key] = user_filter(config=config)
            else:
                self.env.filters[key] = user_filter

        #Load the template file.
        self.template = self.env.get_template(self.template_file+self.ext)


    def export(self, nb):
        """Export notebook object

        nb: Notebook object to export.

        Returns both the converted ipynb file and a dict containing the
        resources created along the way via the transformers and Jinja2
        processing.
        """

        nb, resources = self._preprocess(nb)
        return self.template.render(nb=nb, resources=resources), resources


    def from_filename(self, filename):
        """Read and export a notebook from a filename

        filename: Filename of the notebook file to export.

        Returns both the converted ipynb file and a dict containing the
        resources created along the way via the transformers and Jinja2
        processing.
        """
        with io.open(filename) as f:
            return self.export(nbformat.read(f, 'json'))


    def from_file(self, file_stream):
        """Read and export a notebook from a filename

        file_stream: File handle of file that contains notebook data.

        Returns both the converted ipynb file and a dict containing the
        resources created along the way via the transformers and Jinja2
        processing.
        """

        return self.export(nbformat.read(file_stream, 'json'))


    def _init_environment(self):
        self.env = Environment(
            loader=FileSystemLoader([
                os.path.dirname(os.path.realpath(__file__)) + TEMPLATE_PATH,
                os.path.dirname(os.path.realpath(__file__)) + TEMPLATE_SKELETON_PATH,
                ]),
            extensions=JINJA_EXTENSIONS
            )


    def _register_filters(self, config):
        self.env.filters['indent'] = indent
        self.env.filters['markdown'] = markdown
        
        self.env.filters['ansi2html'] = filters.ansi.ansi2html
        self.env.filters['filter_data_type'] = filters.datatypefilter.DataTypeFilter(config=config)
        self.env.filters['get_lines'] = filters.strings.get_lines 
        self.env.filters['highlight'] = filters.pygments.highlight
        self.env.filters['highlight2html'] = filters.pygments.highlight 
        self.env.filters['highlight2latex'] = filters.pygments.highlight2latex
        self.env.filters['markdown2latex'] = filters.markdown.markdown2latex
        self.env.filters['markdown2rst'] = filters.markdown.markdown2rst
        self.env.filters['pycomment'] = filters.strings.python_comment
        self.env.filters['rm_ansi'] = filters.ansi.remove_ansi
        self.env.filters['rm_dollars'] = filters.strings.strip_dollars
        self.env.filters['rm_fake'] = filters.strings.rm_fake
        self.env.filters['rm_math_space'] = filters.latex.rm_math_space
        self.env.filters['wrap'] = filters.strings.wrap
    

    def _preprocess(self, nb):
        """ Preprocess the notebook using the transformers specific
        for the current export format.

        nb: Notebook to preprocess
        """

        #Dict of 'resources' that can be filled by the preprocessors.
        resources = {}

        #Run each transformer on the notebook.  Carry the output along
        #to each transformer
        for transformer in self.preprocessors:
            nb, resources = transformer(nb, resources)
        return nb, resources

