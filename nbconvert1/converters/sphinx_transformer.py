"""
Module that allows custom Sphinx parameters to be set on the notebook and
on the 'other' object passed into Jinja.
"""
from __future__ import absolute_import

# Used to find Sphinx package location
import sphinx
import os.path

# Used to determine python version
import sys

# Used to set the default date to today's date 
from datetime import date 

# Configurable traitlets
from IPython.utils.traitlets import Unicode, Bool

# Needed for Pygments latex definitions.
from pygments.formatters import LatexFormatter

# Needed to override transformer
from .transformers import (ActivatableTransformer)

class SphinxTransformer(ActivatableTransformer):
    """
    Sphinx utility transformer.

    This transformer is used to set variables needed by the latex to build
    Sphinx stylized templates.
    """
    
    interactive = Bool(True, config=True, help="""
    Allows you to define whether or not the Sphinx exporter will prompt
    you for input during the conversion process.  If this is set to false,
    the author, version, release, date, and chapter_style traits should
    be set.
    """)
    
    author = Unicode("Unknown Author", config=True, help="Author name")
    
    version = Unicode("", config=True, help="""Version number
    You can leave this blank if you do not want to render a version number.
    Example: "1.0.0"
    """)
    
    release = Unicode("", config=True, help="""Release name
    You can leave this blank if you do not want to render a release name.
    Example: "Rough Draft"
    """)
    
    publish_date = Unicode("", config=True, help="""Publish date
    This is the date to render on the document as the publish date.
    Leave this blank to default to todays date.  
    Example: "June 12, 1990"
    """)
    
    chapter_style = Unicode("Bjarne", config=True, help="""Sphinx chapter style
    This is the style to use for the chapter headers in the document.
    You may choose one of the following:
        "Bjarne"    (default)
        "Lenny"
        "Glenn"
        "Conny"
        "Rejne"
        "Sonny"    (used for international documents)
    """)
    
    output_style = Unicode("notebook", config=True, help="""Nbconvert Ipython
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
    
    overridetitle = Unicode("", config=True, help="")
    
    def __call__(self, nb, other):
        """
        Entry
        Since we are not interested in any additional manipulation on a cell
        by cell basis, we do not  call the base implementation.
        """ 
        if self.enabled:
            return self.transform(nb, other)
        else:
            return nb,other

    def transform(self, nb, other):
        """
        Sphinx transformation to apply on each notebook.
        """
         
        # TODO: Add versatile method of additional notebook metadata.  Include
        #       handling of multiple files.  For now use a temporay namespace,
        #       '_draft' to signify that this needs to change.
        if not "_draft" in nb.metadata:
            nb.metadata._draft = {}
            
        if not "sphinx" in other:
            other["sphinx"] = {}

        if self.interactive:
            
            # Prompt the user for additional meta data that doesn't exist currently
            # but would be usefull for Sphinx.
            nb.metadata._draft["author"] = self._prompt_author()
            nb.metadata._draft["version"] = self._prompt_version()
            nb.metadata._draft["release"] = self._prompt_release()
            nb.metadata._draft["date"] = self._prompt_date()
            
            # Prompt the user for the document style.
            other["sphinx"]["chapterstyle"] = self._prompt_chapter_title_style()
            other["sphinx"]["outputstyle"] = self._prompt_output_style()
            
            # Small options
            other["sphinx"]["centeroutput"] = self._prompt_boolean("Do you want to center the output? (false)", False)
            other["sphinx"]["header"] = self._prompt_boolean("Should a Sphinx document header be used? (true)", True)
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
            other["sphinx"]["chapterstyle"] = self.chapter_style
            other["sphinx"]["outputstyle"] = self.output_style
            other["sphinx"]["centeroutput"] = self.center_output
            other["sphinx"]["header"] = self.use_headers
            
        # Find and pass in the path to the Sphinx dependencies.
        other["sphinx"]["texinputs"] = os.path.abspath(sphinx.__file__ + "/../texinputs")
        
        # Generate Pygments definitions for Latex 
        other["sphinx"]["pygment_definitions"] = self._generate_pygments_latex_def()
        
        if not (self.overridetitle == None or len(self.overridetitle.strip()) == 0):
            nb.metadata.name = self.overridetitle
        
        # End
        return nb, other 
    
    def _generate_pygments_latex_def(self):
        return LatexFormatter().get_style_defs()       
    
    def _prompt_author(self):
        return  self._input("Author name: ")
    
    def _prompt_version(self):
        return  self._input("Version (ie ""1.0.0""): ")
    
    def _prompt_release(self):
        return  self._input("Release Name (ie ""Rough draft""): ")
    
    def _prompt_date(self):
        default_date = date.today().strftime("%B %-d, %Y")
        user_date = self._input("Date (deafults to \"" + default_date + "\"): ")
        if len(user_date.strip()) == 0:
            user_date = default_date
        return user_date
    
    def _prompt_boolean(self, prompt, default=False):
        response = self._input(prompt)
        response = response.strip().lower()
        
        #Catch 1, true, yes as True
        if len(response) > 0 and (response == "1" or response[0] == "t" or response[0] == "y"):
            return True
        
        #Catch 0, false, no as False
        elif len(response) > 0 and (response == "0" or response[0] == "f" or response[0] == "n"):
            return False
            
        else:
            return default
        
    def _prompt_output_style(self):
        
        # Dictionary of available output styles
        styles = {1: "simple",
                  2: "notebook"}
        
        #Append comments to the menu when displaying it to the user.
        comments = {1: "(recommended for long code segments)",
                    2: "(default)"}
        
        return self._prompt_dictionary(styles, default_style=2, menu_comments=comments)
    
    def _prompt_chapter_title_style(self):
        
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
        
        return self._prompt_dictionary(styles, menu_comments=comments)
    
    def _prompt_dictionary(self, choices, default_style=1, menu_comments={}):
                
        # Build the menu that will be displayed to the user with
        # all of the options available. 
        prompt = ""
        for key, value in choices.iteritems():
            prompt += "%d %s " % (key, value)
            if key in menu_comments:
                prompt += menu_comments[key]
            prompt += "\n"
        
        # Continue to ask the user for a style until an appropriate
        # one is specified.
        response = -1
        while (not response in choices):
            try:
                text_response = self._input(prompt)
                
                # Use default option if no input.
                if len(text_response.strip()) == 0:
                    response = default_style
                else:
                    response = int(text_response)
            except:
                print("Error: Value is not an available option.  0 selects the default.\n")
        return choices[response]
          
    def _input(self, prompt_text):
        """
        Prompt the user for input.
        
        The input command will change depending on the version of python
        installed.  To maintain support for 2 and earlier, we must use
        raw_input in that case.  Else use input.
        """
        
        # Try to get the python version.  This command is only available in
        # python 2 and later, so it's important that we catch the exception
        # if the command isn't found.
        try:
            majorversion = sys.version_info[0]
        except:
            majorversion = 1
            
        # Use the correct function to prompt the user for input depending on 
        # what python version the code is running in.
        if majorversion >= 3:
            return input(prompt_text) 
        else:
            return raw_input(prompt_text)
