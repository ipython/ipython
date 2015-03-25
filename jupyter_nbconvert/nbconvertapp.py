#!/usr/bin/env python
"""NbConvert is a utility for conversion of .ipynb files.

Command-line interface for the NbConvert conversion utility.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import logging
import sys
import os
import glob

from IPython.core.application import BaseIPythonApplication, base_aliases, base_flags
from IPython.core.profiledir import ProfileDir
from IPython.config import catch_config_error, Configurable
from IPython.utils.traitlets import (
    Unicode, List, Instance, DottedObjectName, Type, CaselessStrEnum, Bool,
)
from IPython.utils.importstring import import_item

from .exporters.export import get_export_names, exporter_map
from IPython.nbconvert import exporters, preprocessors, writers, postprocessors
from .utils.base import NbConvertBase
from .utils.exceptions import ConversionException

#-----------------------------------------------------------------------------
#Classes and functions
#-----------------------------------------------------------------------------

class DottedOrNone(DottedObjectName):
    """
    A string holding a valid dotted object name in Python, such as A.b3._c
    Also allows for None type."""
    
    default_value = u''

    def validate(self, obj, value):
        if value is not None and len(value) > 0:
            return super(DottedOrNone, self).validate(obj, value)
        else:
            return value
            
nbconvert_aliases = {}
nbconvert_aliases.update(base_aliases)
nbconvert_aliases.update({
    'to' : 'NbConvertApp.export_format',
    'template' : 'TemplateExporter.template_file',
    'writer' : 'NbConvertApp.writer_class',
    'post': 'NbConvertApp.postprocessor_class',
    'output': 'NbConvertApp.output_base',
    'reveal-prefix': 'RevealHelpPreprocessor.url_prefix',
    'nbformat': 'NotebookExporter.nbformat_version',
})

nbconvert_flags = {}
nbconvert_flags.update(base_flags)
nbconvert_flags.update({
    'execute' : (
        {'ExecutePreprocessor' : {'enabled' : True}},
        "Execute the notebook prior to export."
        ),
    'stdout' : (
        {'NbConvertApp' : {'writer_class' : "StdoutWriter"}},
        "Write notebook output to stdout instead of files."
        ),
    'inplace' : (
        {
            'NbConvertApp' : {'use_output_suffix' : False},
            'FilesWriter': {'build_directory': ''}
        },
        """Run nbconvert in place, overwriting the existing notebook (only 
        relevant when converting to notebook format)"""
        )
})


class NbConvertApp(BaseIPythonApplication):
    """Application used to convert from notebook file type (``*.ipynb``)"""

    name = 'ipython-nbconvert'
    aliases = nbconvert_aliases
    flags = nbconvert_flags
    
    def _log_level_default(self):
        return logging.INFO
    
    def _classes_default(self):
        classes = [NbConvertBase, ProfileDir]
        for pkg in (exporters, preprocessors, writers, postprocessors):
            for name in dir(pkg):
                cls = getattr(pkg, name)
                if isinstance(cls, type) and issubclass(cls, Configurable):
                    classes.append(cls)
        
        return classes

    description = Unicode(
        u"""This application is used to convert notebook files (*.ipynb)
        to various other formats.

        WARNING: THE COMMANDLINE INTERFACE MAY CHANGE IN FUTURE RELEASES.""")

    output_base = Unicode('', config=True, help='''overwrite base name use for output files.
            can only be used when converting one notebook at a time.
            ''')

    use_output_suffix = Bool(
        True, 
        config=True,
        help="""Whether to apply a suffix prior to the extension (only relevant
            when converting to notebook format). The suffix is determined by
            the exporter, and is usually '.nbconvert'.""")

    examples = Unicode(u"""
        The simplest way to use nbconvert is
        
        > ipython nbconvert mynotebook.ipynb
        
        which will convert mynotebook.ipynb to the default format (probably HTML).
        
        You can specify the export format with `--to`.
        Options include {0}
        
        > ipython nbconvert --to latex mynotebook.ipynb

        Both HTML and LaTeX support multiple output templates. LaTeX includes
        'base', 'article' and 'report'.  HTML includes 'basic' and 'full'. You
        can specify the flavor of the format used.

        > ipython nbconvert --to html --template basic mynotebook.ipynb
        
        You can also pipe the output to stdout, rather than a file
        
        > ipython nbconvert mynotebook.ipynb --stdout

        PDF is generated via latex

        > ipython nbconvert mynotebook.ipynb --to pdf
        
        You can get (and serve) a Reveal.js-powered slideshow
        
        > ipython nbconvert myslides.ipynb --to slides --post serve
        
        Multiple notebooks can be given at the command line in a couple of 
        different ways:
  
        > ipython nbconvert notebook*.ipynb
        > ipython nbconvert notebook1.ipynb notebook2.ipynb
        
        or you can specify the notebooks list in a config file, containing::
        
            c.NbConvertApp.notebooks = ["my_notebook.ipynb"]
        
        > ipython nbconvert --config mycfg.py
        """.format(get_export_names()))

    # Writer specific variables
    writer = Instance('IPython.nbconvert.writers.base.WriterBase',  
                      help="""Instance of the writer class used to write the 
                      results of the conversion.""")
    writer_class = DottedObjectName('FilesWriter', config=True, 
                                    help="""Writer class used to write the 
                                    results of the conversion""")
    writer_aliases = {'fileswriter': 'IPython.nbconvert.writers.files.FilesWriter',
                      'debugwriter': 'IPython.nbconvert.writers.debug.DebugWriter',
                      'stdoutwriter': 'IPython.nbconvert.writers.stdout.StdoutWriter'}
    writer_factory = Type()

    def _writer_class_changed(self, name, old, new):
        if new.lower() in self.writer_aliases:
            new = self.writer_aliases[new.lower()]
        self.writer_factory = import_item(new)

    # Post-processor specific variables
    postprocessor = Instance('IPython.nbconvert.postprocessors.base.PostProcessorBase',  
                      help="""Instance of the PostProcessor class used to write the 
                      results of the conversion.""")

    postprocessor_class = DottedOrNone(config=True, 
                                    help="""PostProcessor class used to write the 
                                    results of the conversion""")
    postprocessor_aliases = {'serve': 'IPython.nbconvert.postprocessors.serve.ServePostProcessor'}
    postprocessor_factory = Type()

    def _postprocessor_class_changed(self, name, old, new):
        if new.lower() in self.postprocessor_aliases:
            new = self.postprocessor_aliases[new.lower()]
        if new:
            self.postprocessor_factory = import_item(new)


    # Other configurable variables
    export_format = CaselessStrEnum(get_export_names(),
        default_value="html",
        config=True,
        help="""The export format to be used."""
    )

    notebooks = List([], config=True, help="""List of notebooks to convert.
                     Wildcards are supported.
                     Filenames passed positionally will be added to the list.
                     """)

    @catch_config_error
    def initialize(self, argv=None):
        self.init_syspath()
        super(NbConvertApp, self).initialize(argv)
        self.init_notebooks()
        self.init_writer()
        self.init_postprocessor()



    def init_syspath(self):
        """
        Add the cwd to the sys.path ($PYTHONPATH)
        """
        sys.path.insert(0, os.getcwd())
        

    def init_notebooks(self):
        """Construct the list of notebooks.
        If notebooks are passed on the command-line,
        they override notebooks specified in config files.
        Glob each notebook to replace notebook patterns with filenames.
        """

        # Specifying notebooks on the command-line overrides (rather than adds)
        # the notebook list
        if self.extra_args:
            patterns = self.extra_args
        else:
            patterns = self.notebooks

        # Use glob to replace all the notebook patterns with filenames.
        filenames = []
        for pattern in patterns:
            
            # Use glob to find matching filenames.  Allow the user to convert 
            # notebooks without having to type the extension.
            globbed_files = glob.glob(pattern)
            globbed_files.extend(glob.glob(pattern + '.ipynb'))
            if not globbed_files:
                self.log.warn("pattern %r matched no files", pattern)

            for filename in globbed_files:
                if not filename in filenames:
                    filenames.append(filename)
        self.notebooks = filenames

    def init_writer(self):
        """
        Initialize the writer (which is stateless)
        """
        self._writer_class_changed(None, self.writer_class, self.writer_class)
        self.writer = self.writer_factory(parent=self)
        if hasattr(self.writer, 'build_directory') and self.writer.build_directory != '':
            self.use_output_suffix = False

    def init_postprocessor(self):
        """
        Initialize the postprocessor (which is stateless)
        """
        self._postprocessor_class_changed(None, self.postprocessor_class, 
            self.postprocessor_class)
        if self.postprocessor_factory:
            self.postprocessor = self.postprocessor_factory(parent=self)

    def start(self):
        """
        Ran after initialization completed
        """
        super(NbConvertApp, self).start()
        self.convert_notebooks()

    def init_single_notebook_resources(self, notebook_filename):
        """Step 1: Initialize resources

        This intializes the resources dictionary for a single notebook. This
        method should return the resources dictionary, and MUST include the
        following keys:

            - profile_dir: the location of the profile directory
            - unique_key: the notebook name
            - output_files_dir: a directory where output files (not including
              the notebook itself) should be saved

        """

        # Get a unique key for the notebook and set it in the resources object.
        basename = os.path.basename(notebook_filename)
        notebook_name = basename[:basename.rfind('.')]
        if self.output_base:
            # strip duplicate extension from output_base, to avoid Basname.ext.ext
            if getattr(self.exporter, 'file_extension', False):
                base, ext = os.path.splitext(self.output_base)
                if ext == self.exporter.file_extension:
                    self.output_base = base
            notebook_name = self.output_base

        self.log.debug("Notebook name is '%s'", notebook_name)

        # first initialize the resources we want to use
        resources = {}
        resources['profile_dir'] = self.profile_dir.location
        resources['unique_key'] = notebook_name
        resources['output_files_dir'] = '%s_files' % notebook_name

        return resources

    def export_single_notebook(self, notebook_filename, resources):
        """Step 2: Export the notebook

        Exports the notebook to a particular format according to the specified
        exporter. This function returns the output and (possibly modified)
        resources from the exporter.

        """
        try:
            output, resources = self.exporter.from_filename(notebook_filename, resources=resources)
        except ConversionException:
            self.log.error("Error while converting '%s'", notebook_filename, exc_info=True)
            self.exit(1)

        return output, resources

    def write_single_notebook(self, output, resources):
        """Step 3: Write the notebook to file

        This writes output from the exporter to file using the specified writer.
        It returns the results from the writer.

        """
        if 'unique_key' not in resources:
            raise KeyError("unique_key MUST be specified in the resources, but it is not")

        notebook_name = resources['unique_key']
        if self.use_output_suffix and not self.output_base:
            notebook_name += resources.get('output_suffix', '')

        write_results = self.writer.write(
            output, resources, notebook_name=notebook_name)
        return write_results

    def postprocess_single_notebook(self, write_results):
        """Step 4: Postprocess the notebook

        This postprocesses the notebook after it has been written, taking as an
        argument the results of writing the notebook to file. This only actually
        does anything if a postprocessor has actually been specified.

        """
        # Post-process if post processor has been defined.
        if hasattr(self, 'postprocessor') and self.postprocessor:
            self.postprocessor(write_results)

    def convert_single_notebook(self, notebook_filename):
        """Convert a single notebook. Performs the following steps:

            1. Initialize notebook resources
            2. Export the notebook to a particular format
            3. Write the exported notebook to file
            4. (Maybe) postprocess the written file

        """
        self.log.info("Converting notebook %s to %s", notebook_filename, self.export_format)
        resources = self.init_single_notebook_resources(notebook_filename)
        output, resources = self.export_single_notebook(notebook_filename, resources)
        write_results = self.write_single_notebook(output, resources)
        self.postprocess_single_notebook(write_results)

    def convert_notebooks(self):
        """
        Convert the notebooks in the self.notebook traitlet
        """
        # check that the output base isn't specified if there is more than
        # one notebook to convert
        if self.output_base != '' and len(self.notebooks) > 1:
            self.log.error(
                """
                UsageError: --output flag or `NbConvertApp.output_base` config option
                cannot be used when converting multiple notebooks.
                """
            )
            self.exit(1)
        
        # initialize the exporter
        self.exporter = exporter_map[self.export_format](config=self.config)

        # no notebooks to convert!
        if len(self.notebooks) == 0:
            self.print_help()
            sys.exit(-1)

        # convert each notebook
        for notebook_filename in self.notebooks:
            self.convert_single_notebook(notebook_filename)
            
#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

launch_new_instance = NbConvertApp.launch_instance
