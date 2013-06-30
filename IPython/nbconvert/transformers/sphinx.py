"""Module that allows custom Sphinx parameters to be set on the notebook and
on the 'other' object passed into Jinja.  Called prior to Jinja conversion
process.
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
# Used to find Sphinx package location
import sphinx
import os.path

# Used to set the default date to today's date 
from datetime import date 

# Third-party imports
# Needed for Pygments latex definitions.
from pygments.formatters import LatexFormatter

# Our own imports
# Configurable traitlets
from IPython.utils.traitlets import Unicode, Bool

# Needed to override transformer
from .activatable import (ActivatableTransformer) #TODO

import nbconvert.utils.console  

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class SphinxTransformer(ActivatableTransformer):
    """
    Sphinx utility transformer.

    This transformer is used to set variables needed by the latex to build
    Sphinx stylized templates.
    """
    
    interactive = Bool(False, config=True, help="""
        Allows you to define whether or not the Sphinx exporter will prompt
        you for input during the conversion process.  If this is set to false,
        the author, version, release, date, and chapter_style traits should
        be set.
        """)
    
    author = Unicode("Unknown Author", config=True, help="Author name")
    
    version = Unicode("", config=True, help="""
        Version number
        You can leave this blank if you do not want to render a version number.
        Example: "1.0.0"
        """)
    
    release = Unicode("", config=True, help="""
        Release name
        You can leave this blank if you do not want to render a release name.
        Example: "Rough Draft"
        """)
    
    publish_date = Unicode("", config=True, help="""
        Publish date
        This is the date to render on the document as the publish date.
        Leave this blank to default to todays date.  
        Example: "June 12, 1990"
        """)
    
    chapter_style = Unicode("Bjarne", config=True, help="""
        Sphinx chapter style
        This is the style to use for the chapter headers in the document.
        You may choose one of the following:
            "Bjarne"    (default)
            "Lenny"
            "Glenn"
            "Conny"
            "Rejne"
            "Sonny"    (used for international documents)
        """)
    
    output_style = Unicode("notebook", config=True, help="""
        Nbconvert Ipython
        notebook input/output formatting style.
        You may choose one of the following:
            "simple     (recommended for long code segments)"
            "notebook"  (default)
        """)
    
    center_output = Bool(False, config=True, help="""
        Optional attempt to center all output.  If this is false, no additional
        formatting is applied.
        """)
    
    use_headers = Bool(True, config=True, help="""
        Whether not a header should be added to the document.
        """)
    
    #Allow the user to override the title of the notebook (useful for
    #fancy document titles that the file system doesn't support.)
    overridetitle = Unicode("", config=True, help="")

    
    def call(self, nb, resources):
        """
        Sphinx transformation to apply on each notebook.
        
        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            transformers to pass variables into the Jinja engine.
        """
         
        # TODO: Add versatile method of additional notebook metadata.  Include
        #       handling of multiple files.  For now use a temporay namespace,
        #       '_draft' to signify that this needs to change.
        if not "_draft" in nb.metadata:
            nb.metadata._draft = {}
            
        if not "sphinx" in resources:
            resources["sphinx"] = {}

        if self.interactive:
            
            # Prompt the user for additional meta data that doesn't exist currently
            # but would be usefull for Sphinx.
            nb.metadata._draft["author"] = self._prompt_author()
            nb.metadata._draft["version"] = self._prompt_version()
            nb.metadata._draft["release"] = self._prompt_release()
            nb.metadata._draft["date"] = self._prompt_date()
            
            # Prompt the user for the document style.
            resources["sphinx"]["chapterstyle"] = self._prompt_chapter_title_style()
            resources["sphinx"]["outputstyle"] = self._prompt_output_style()
            
            # Small options
            resources["sphinx"]["centeroutput"] = nbconvert.utils.console.prompt_boolean("Do you want to center the output? (false)", False)
            resources["sphinx"]["header"] = nbconvert.utils.console.prompt_boolean("Should a Sphinx document header be used? (true)", True)
        else:
            
            # Try to use the traitlets.
            nb.metadata._draft["author"] = self.author
            nb.metadata._draft["version"] = self.version
            nb.metadata._draft["release"] = self.release
            
            # Use todays date if none is provided.
            if len(self.publish_date.strip()) == 0:
                nb.metadata._draft["date"] = date.today().strftime("%B %-d, %Y")
            else:
                nb.metadata._draft["date"] = self.publish_date
            
            # Sphinx traitlets.
            resources["sphinx"]["chapterstyle"] = self.chapter_style
            resources["sphinx"]["outputstyle"] = self.output_style
            resources["sphinx"]["centeroutput"] = self.center_output
            resources["sphinx"]["header"] = self.use_headers
            
        # Find and pass in the path to the Sphinx dependencies.
        resources["sphinx"]["texinputs"] = os.path.abspath(sphinx.__file__ + "/../texinputs")
        
        # Generate Pygments definitions for Latex 
        resources["sphinx"]["pygment_definitions"] = self._generate_pygments_latex_def()
        
        if not (self.overridetitle == None or len(self.overridetitle.strip()) == 0):
            nb.metadata.name = self.overridetitle
        
        # End
        return nb, resources 
    
    
    def _generate_pygments_latex_def(self):
        """
        Generate the pygments latex definitions that allows pygments
        to work in latex.
        """
        
        return LatexFormatter().get_style_defs()       
    
    
    def _prompt_author(self):
        """
        Prompt the user to input an Author name
        """
        return  nbconvert.utils.console.input("Author name: ")
    
    
    def _prompt_version(self):
        """
        prompt the user to enter a version number
        """
        return  nbconvert.utils.console.input("Version (ie ""1.0.0""): ")
    
    
    def _prompt_release(self):
        """
        Prompt the user to input a release name
        """
        
        return  nbconvert.utils.console.input("Release Name (ie ""Rough draft""): ")
    
    
    def _prompt_date(self):
        """
        Prompt the user to enter a date
        """
        
        default_date = date.today().strftime("%B %-d, %Y")
        user_date = nbconvert.utils.console.input("Date (deafults to \"" + default_date + "\"): ")
        if len(user_date.strip()) == 0:
            user_date = default_date
        return user_date
    
    
    def _prompt_output_style(self):
        """
        Prompts the user to pick an IPython output style.
        """
        
        # Dictionary of available output styles
        styles = {1: "simple",
                  2: "notebook"}
        
        #Append comments to the menu when displaying it to the user.
        comments = {1: "(recommended for long code segments)",
                    2: "(default)"}
        
        return nbconvert.utils.console.prompt_dictionary(styles, default_style=2, menu_comments=comments)
    
    
    def _prompt_chapter_title_style(self):
        """
        Prompts the user to pick a Sphinx chapter style
        """
        
        # Dictionary of available Sphinx styles
        styles = {1: "Bjarne",
                  2: "Lenny",
                  3: "Glenn",
                  4: "Conny",
                  5: "Rejne",
                  6: "Sonny"}
        
        #Append comments to the menu when displaying it to the user.
        comments = {1: "(default)",
                    6: "(for international documents)"}
        
        return nbconvert.utils.console.prompt_dictionary(styles, menu_comments=comments)

