"""Utility functions for interacting with the console"""
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

# Used to determine python version
import sys

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------
            
def input(prompt_text):
    """
    Prompt the user for input.
    
    The input command will change depending on the version of python
    installed.  To maintain support for 2 and earlier, we must use
    raw_input in that case.  Else use input.
    
    Parameters
    ----------
    prompt_text : str
        Prompt to display to the user.
    """
    
    # Try to get the python version.  This command is only available in
    # python 2 and later, so it's important that we catch the exception
    # if the command isn't found.
    try:
        majorversion = sys.version_info[0]
    except AttributeError:
        majorversion = 1
        
    # Use the correct function to prompt the user for input depending on 
    # what python version the code is running in.
    if majorversion >= 3:
        return input(prompt_text) 
    else:
        return raw_input(prompt_text).decode(sys.stdin.encoding)

    
def prompt_boolean(prompt, default=False):
    """
    Prompt the user for a boolean response.
    
    Parameters
    ----------
    prompt : str
        prompt to display to the user
    default : bool, optional
        response to return if none is given by the user
    """
    
    response = input(prompt)
    response = response.strip().lower()
    
    #Catch 1, true, yes as True
    if len(response) > 0 and (response == "1" or response[0] == "t" or response[0] == "y"):
        return True
    
    #Catch 0, false, no as False
    elif len(response) > 0 and (response == "0" or response[0] == "f" or response[0] == "n"):
        return False
        
    else:
        return default


def prompt_dictionary(choices, default_style=1, menu_comments={}):
    """
    Prompt the user to chose one of many selections from a menu.
    
    Parameters
    ----------
    choices : dictionary
        Keys - choice numbers (int)
        Values - choice value (str), this is what the function will return
    default_style : int, optional
        Choice to select if the user doesn't respond
    menu_comments : dictionary, optional
        Additional comments to append to the menu as it is displayed
        in the console.
        Keys - choice numbers (int)
        Values - comment (str), what will be appended to the 
        corresponding choice
    """
            
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
            text_response = input(prompt)
            
            # Use default option if no input.
            if len(text_response.strip()) == 0:
                response = default_style
            else:
                response = int(text_response)
        except ValueError:
            print("Error: Value is not an available option.  0 selects the default.\n")
    return choices[response]
