from .widget import Widget, DOMWidget, CallbackDispatcher, register

from .widget_bool import Checkbox, ToggleButton
from .widget_button import Button
from .widget_box import Box, FlexBox, HBox, VBox
from .widget_float import FloatText, BoundedFloatText, FloatSlider, FloatProgress, FloatRangeSlider
from .widget_image import Image
from .widget_int import IntText, BoundedIntText, IntSlider, IntProgress, IntRangeSlider
from .widget_output import Output
from .widget_selection import RadioButtons, ToggleButtons, Dropdown, Select, SelectMultiple
from .widget_selectioncontainer import Tab, Accordion
from .widget_string import HTML, Latex, Text, Textarea
from .interaction import interact, interactive, fixed, interact_manual
from .widget_link import jslink, jsdlink

# Deprecated classes
from .widget_bool import CheckboxWidget, ToggleButtonWidget
from .widget_button import ButtonWidget
from .widget_box import ContainerWidget
from .widget_float import FloatTextWidget, BoundedFloatTextWidget, FloatSliderWidget, FloatProgressWidget
from .widget_image import ImageWidget
from .widget_int import IntTextWidget, BoundedIntTextWidget, IntSliderWidget, IntProgressWidget
from .widget_selection import RadioButtonsWidget, ToggleButtonsWidget, DropdownWidget, SelectWidget
from .widget_selectioncontainer import TabWidget, AccordionWidget
from .widget_string import HTMLWidget, LatexWidget, TextWidget, TextareaWidget

# We use warn_explicit so we have very brief messages without file or line numbers.
# The concern is that file or line numbers will confuse the interactive user.
# To ignore this warning, do:
#
#     from warnings import filterwarnings
#     filterwarnings('ignore', module='IPython.html.widgets')

from warnings import warn_explicit
__warningregistry__ = {}
warn_explicit("IPython widgets are experimental and may change in the future.",
              FutureWarning, '', 0, module = 'IPython.html.widgets',
              registry = __warningregistry__, module_globals = globals)
