"""
Module that allows latex output notebooks to be conditioned before 
they are converted.
"""

# Configurable traitlets
from IPython.utils.traitlets import Unicode, Bool

# Needed to override transformer
from converters.transformers import (ActivatableTransformer)

class LatexTransformer(ActivatableTransformer):
    """
    Converter for latex destined documents.
    """    
    
    def __call__(self, nb, other):
        """
        Entrypoint
        
        nb - Input notebook
        other - Maps to 'resources' in Jinja
        """
        
        # Only run if enabled.
        if self.enabled:
            return self.Transform(nb, other)
            
    def Transform(self, nb, other):
        """
        Transform the notebook to make it compatible with markdown2latex.
        """
        
        #Fix the markdown in every markdown cell.
        for sheet in nb.worksheets:
            for cell in sheet.cells:
                if hasattr(cell, "source") and cell.cell_type == "markdown":
                    cell.source = self.remove_math_space(cell.source)
        return nb, other
    
    def remove_math_space(self, text):
        """
        Remove the space between latex math commands and enclosing $ symbols.
        """
        
        # First, scan through the markdown looking for $.  If
        # a $ symbol is found, without a preceding \, assume
        # it is the start of a math block.  UNLESS that $ is
        # not followed by another within two math_lines.
        math_regions = []
        math_lines = 0
        within_math = False
        math_start_index = 0
        index = 0
        last_character = ""
        for char in text: #Loop through each character in the text.
            
            #Make sure the character isn't preceeded by a backslash
            if (char == "$" and last_character != "\\"):
                
                # Close the math region if this is an ending $
                if within_math:
                    within_math = False
                    math_regions.append([math_start_index, index+1])
                else:
                    
                    # Start a new math region
                    within_math = True
                    math_start_index = index
                    math_lines = 0
                    
            # If we are in a math region, count the number of lines parsed.
            # Cancel the math region if we find two line breaks!
            elif char == "\n":
                if within_math:
                    math_lines += 1
                    if math_lines > 1:
                        within_math = False
                        
            # Remember the last character so we can easily watch
            # for backslashes
            last_character = char
            
            # Next index
            index += 1
        
        # Reset the index and last char
        index = 0
        
        # Now that we know what regions of the text are math and
        # what regions aren't, we can separate them into "blocks"
        text_blocks=[]
        math_blocks=[]
        was_math_block = False
        current_block = ""
        for char in text:
            
            # Check if this is a math region.
            ismath = False
            for keypair in math_regions:
                if (keypair[0] <= index and index <=  keypair[1]):
                    ismath = True
            
            # If the region type has changed since the last
            # iteration, commit all read characters to that
            # region type and reset the buffer.
            if (ismath and not was_math_block):
                was_math_block = True
                text_blocks.append(current_block)
                current_block=""
            elif ((not ismath) and was_math_block):
                was_math_block = False
                math_blocks.append(current_block)
                current_block=""
            
            # Store the character
            current_block += char
            
            # Next index
            index += 1
            
        # Save whatever remains in the buffer that hasn't yet been saved.
        if was_math_block:
            math_blocks.append(current_block)
        else:
            text_blocks.append(current_block)
            
        # Recombine the regions, while processing every math region, removing
        # the spaces between the math and the $ symbols.
        output = ""
        for index in range(0,len(text_blocks) + len(math_blocks)):
            if index % 2 == 0:
                output += text_blocks[index/2]
            else:
                mathblock = math_blocks[(index -1)/2]
                mathblock = mathblock[1:len(mathblock)-2]
                output += "$" + mathblock.strip() + "$"
        return output
        