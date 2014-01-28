Notebook Widgets
----------------

Available in the new `IPython.html.widgets` namespace, widgets provide an easy
way for IPython notebook users to display GUI controls in the IPython notebook.
IPython comes with bundle of built-in widgets and also the ability for users
to define their own widgets.  A widget is displayed in the front-end using
using a view.  For example, a FloatRangeWidget can be displayed using a
FloatSliderView (which is the default if no view is specified when displaying
the widget).  IPython also comes with a bundle of views and the ability for the
user to define custom views.  One widget can be displayed multiple times, in on
or more cells, using one or more views.  All views will automatically remain in
sync with the widget which is accessible in the back-end.

The widget layer provides an MVC-like architecture on top of the comm layer. 
It's useful for widgets that can be expressed via a list of properties. 
Widgets work by synchronizing IPython traitlet models in the back-end with 
backbone models in the front-end. The widget layer automatically handles

* delta compression (only sending the state information that has changed)
* wiring the message callbacks to the correct cells automatically
* inter-view synchronization (handled by backbone)
* message throttling (to avoid flooding the kernel)
* parent/child relationships between views (which one can override to specify custom parent/child relationships)
* ability to manipulate the widget view's DOM from python using CSS, $().addClass, and $().removeClass methods
