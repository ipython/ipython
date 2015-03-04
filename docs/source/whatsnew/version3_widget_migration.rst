Migrating Widgets to IPython 3
==============================

Upgrading Notebooks
-------------------

1. The first thing you'll notice when upgrading an IPython 2.0 widget
   notebook to IPython 3.0 is the "Notebook converted" dialog. Click
   "ok".
2. All of the widgets distributed with IPython have been renamed. The
   "Widget" suffix was removed from the end of the class name. i.e.
   ``ButtonWidget`` is now ``Button``.
3. ``ContainerWidget`` was renamed to ``Box``.
4. ``PopupWidget`` was removed from IPython. If you use the
   ``PopupWidget``, try using a ``Box`` widget instead. If your notebook
   can't live without the popup functionality, subclass the ``Box``
   widget (both in Python and JS) and use JQuery UI's ``draggable()``
   and ``resizable()`` methods to mimic the behavior.
5. ``add_class`` and ``remove_class`` were removed. More often than not
   a new attribute exists on the widget that allows you to achieve the
   same explicitly. i.e. the ``Button`` widget now has a
   ``button_style`` attribute which you can set to 'primary', 'success',
   'info', 'warning', 'danger', or '' instead of using ``add_class`` to
   add the bootstrap class. ``VBox`` and ``HBox`` classes (flexible
   ``Box`` subclasses) were added that allow you to avoid using
   ``add_class`` and ``remove_class`` to make flexible box model
   layouts. As a last resort, if you can't find a built in attribute for
   the class you want to use, a new ``_dom_classes`` list trait was
   added, which combines ``add_class`` and ``remove_class`` into one
   stateful list.
6. ``set_css`` and ``get_css`` were removed in favor of explicit style
   attributes - ``visible``, ``width``, ``height``, ``padding``,
   ``margin``, ``color``, ``background_color``, ``border_color``,
   ``border_width``, ``border_radius``, ``border_style``,
   ``font_style``, ``font_weight``, ``font_size``, and ``font_family``
   are a few. If you can't find a trait to see the css attribute you
   need, you can, in order of preference, (A) subclass to create your
   own custom widget, (B) use CSS and the ``_dom_classes`` trait to set
   ``_dom_classes``, or (C) use the ``_css`` dictionary to set CSS
   styling like ``set_css`` and ``get_css``.
7. For selection widgets, such as ``Dropdown``, the ``values`` argument
   has been renamed to ``options``.

Upgrading Custom Widgets
------------------------

Javascript
~~~~~~~~~~

1. If you are distributing your widget and decide to use the deferred
   loading technique (preferred), you can remove all references to the
   WidgetManager and the register model/view calls (see the Python
   section below for more information).
2. In 2.0 require.js was used incorrectly, that has been fixed and now
   loading works more like Python's import. Requiring
   ``widgets/js/widget`` doesn't import the ``WidgetManager`` class,
   instead it imports a dictionary that exposes the classes within that
   module:

   .. code:: javascript

       {
       'WidgetModel': WidgetModel,
       'WidgetView': WidgetView,
       'DOMWidgetView': DOMWidgetView,
       'ViewList': ViewList,
       }

   If you decide to continue to use the widget registry (by registering
   your widgets with the manager), you can import a dictionary with a
   handle to the WidgetManager class by requiring
   ``widgets/js/manager``. Doing so will import:

   .. code:: javascript

       {'WidgetManager': WidgetManager}

3. Don't rely on the ``IPython`` namespace for anything. To inherit from
   the DOMWidgetView, WidgetView, or WidgetModel, require
   ``widgets/js/widget`` as ``widget``. If you were inheriting from
   DOMWidgetView, and the code looked like this:

   .. code:: javascript

       IPython.DOMWidgetView.extend({...})

   It would become this:

   .. code:: javascript

       widget.DOMWidgetView.extend({...})

4. Custom models are encouraged. When possible, it's recommended to move
   your code into a custom model, so actions are performed 1 time,
   instead of N times where N is the number of displayed views.

Python
~~~~~~

Generally, custom widget Python code can remain unchanged. If you
distribute your custom widget, you may be using ``display`` and
``Javascript`` to publish the widget's Javascript to the front-end. That
is no longer the recommended way of distributing widget Javascript.
Instead have the user install the Javascript to his/her nbextension
directory or their profile's static directory. Then use the new
``_view_module`` and ``_model_module`` traitlets in combination with
``_view_name`` and ``_model_name`` to instruct require.js on how to load
the widget's Javascript. The Javascript is then loaded when the widget
is used for the first time.

Details
-------

Asynchronous
~~~~~~~~~~~~

In the IPython 2.x series the only way to register custom widget views
and models was to use the registry in the widget manager. Unfortunately,
using this method made distributing and running custom widgets difficult. The widget
maintainer had to either use the rich display framework to push the
widget's Javascript to the notebook or instruct the users to install the
Javascript by hand in a custom profile. With the first method, the
maintainer would have to be careful about when the Javascript was pushed
to the front-end. If the Javascript was pushed on Python widget
``import``, the widgets wouldn't work after page refresh. This is
because refreshing the page does not restart the kernel, and the Python
``import`` statement only runs once in a given kernel instance (unless
you reload the Python modules, which isn't straight forward). This meant
the maintainer would have to have a separate ``push_js()`` method that
the user would have to call after importing the widget's Python code.

Our solution was to add support for loading widget views and models
using require.js paths. Thus the comm and widget frameworks now support
lazy loading. To do so, everything had to be converted to asynchronous
code. HTML5 promises are used to accomplish that
(`#6818 <https://github.com/ipython/ipython/pull/6818>`__,
`#6914 <https://github.com/ipython/ipython/pull/6914>`__).

Symmetry
~~~~~~~~

In IPython 3.0, widgets can be instantiated from the front-end
(`#6664 <https://github.com/ipython/ipython/pull/6664>`__). On top of
this, a widget persistence API was added
(`#7163 <https://github.com/ipython/ipython/pull/7163>`__,
`#7227 <https://github.com/ipython/ipython/pull/7227>`__). With the
widget persistence API, you can persist your widget instances using
Javascript. This makes it easy to persist your widgets to your notebook
document (with a small amount of custom JS). By default, the widgets are
persisted to your web browsers local storage which makes them reappear
when your refresh the page.

Smaller Changes
~~~~~~~~~~~~~~~

-  Latex math is supported in widget ``description``\ s
   (`#5937 <https://github.com/ipython/ipython/pull/5937>`__).
-  Widgets can be display more than once within a single container
   widget (`#5963 <https://github.com/ipython/ipython/pull/5963>`__,
   `#6990 <https://github.com/ipython/ipython/pull/6990>`__).
-  ``FloatRangeSlider`` and ``IntRangeSlider`` were added
   (`#6050 <https://github.com/ipython/ipython/pull/6050>`__).
-  "Widget" was removed from the ends of all of the widget class names
   (`#6125 <https://github.com/ipython/ipython/pull/6125>`__).
-  ``ContainerWidget`` was renamed to ``Box``
   (`#6125 <https://github.com/ipython/ipython/pull/6125>`__).
-  ``HBox`` and ``VBox`` widgets were added
   (`#6125 <https://github.com/ipython/ipython/pull/6125>`__).
-  ``add\_class`` and ``remove\_class`` were removed in favor of a
   ``_dom_classes`` list
   (`#6235 <https://github.com/ipython/ipython/pull/6235>`__).
-  ``get\_css`` and ``set\_css`` were removed in favor of explicit
   traits for widget styling
   (`#6235 <https://github.com/ipython/ipython/pull/6235>`__).
-  ``jslink`` and ``jsdlink`` were added
   (`#6454 <https://github.com/ipython/ipython/pull/6454>`__,
   `#7468 <https://github.com/ipython/ipython/pull/7468>`__).
-  An ``Output`` widget was added, which allows you to ``print`` and
   ``display`` within widgets
   (`#6670 <https://github.com/ipython/ipython/pull/6670>`__).
-  ``PopupWidget`` was removed
   (`#7341 <https://github.com/ipython/ipython/pull/7341>`__).
-  A visual cue was added for widgets with 'dead' comms
   (`#7227 <https://github.com/ipython/ipython/pull/7227>`__).
-  A ``SelectMultiple`` widget was added (a ``Select`` widget that
   allows multiple things to be selected at once)
   (`#6890 <https://github.com/ipython/ipython/pull/6890>`__).
-  A class was added to help manage children views
   (`#6990 <https://github.com/ipython/ipython/pull/6990>`__).
-  A warning was added that shows on widget import because it's expected
   that the API will change again by IPython 4.0. This warning can be
   supressed (`#7107 <https://github.com/ipython/ipython/pull/7107>`__,
   `#7200 <https://github.com/ipython/ipython/pull/7200>`__,
   `#7201 <https://github.com/ipython/ipython/pull/7201>`__,
   `#7204 <https://github.com/ipython/ipython/pull/7204>`__).

Comm and Widget PR Index
------------------------

Here is a chronological list of PRs affecting the widget and comm frameworks for IPython 3.0. Note that later PRs may revert changes
made in earlier PRs:

- Add placeholder attribute to text widgets
  `#5652 <https://github.com/ipython/ipython/pull/5652>`__
- Add latex support in widget labels,
  `#5937 <https://github.com/ipython/ipython/pull/5937>`__
- Allow widgets to display more than once within container widgets.
  `#5963 <https://github.com/ipython/ipython/pull/5963>`__
- use require.js,
  `#5980 <https://github.com/ipython/ipython/pull/5980>`__
- Range widgets
  `#6050 <https://github.com/ipython/ipython/pull/6050>`__
- Interact on\_demand option
  `#6051 <https://github.com/ipython/ipython/pull/6051>`__
- Allow text input on slider widgets
  `#6106 <https://github.com/ipython/ipython/pull/6106>`__
- support binary buffers in comm messages
  `#6110 <https://github.com/ipython/ipython/pull/6110>`__
- Embrace the flexible box model in the widgets
  `#6125 <https://github.com/ipython/ipython/pull/6125>`__
- Widget trait serialization
  `#6128 <https://github.com/ipython/ipython/pull/6128>`__
- Make Container widgets take children as the first positional
  argument `#6153 <https://github.com/ipython/ipython/pull/6153>`__
- once-displayed
  `#6168 <https://github.com/ipython/ipython/pull/6168>`__
- Validate slider value, when limits change
  `#6171 <https://github.com/ipython/ipython/pull/6171>`__
- Unregistering comms in Comm Manager
  `#6216 <https://github.com/ipython/ipython/pull/6216>`__
- Add EventfulList and EventfulDict trait types.
  `#6228 <https://github.com/ipython/ipython/pull/6228>`__
- Remove add/remove\_class and set/get\_css.
  `#6235 <https://github.com/ipython/ipython/pull/6235>`__
- avoid unregistering widget model twice
  `#6250 <https://github.com/ipython/ipython/pull/6250>`__
- Widget property lock should compare json states, not python states
  `#6332 <https://github.com/ipython/ipython/pull/6332>`__
- Strip the IPY\_MODEL\_ prefix from widget IDs before referencing
  them. `#6377 <https://github.com/ipython/ipython/pull/6377>`__
- "event" is not defined error in Firefox
  `#6437 <https://github.com/ipython/ipython/pull/6437>`__
- Javascript link
  `#6454 <https://github.com/ipython/ipython/pull/6454>`__
- Bulk update of widget attributes
  `#6463 <https://github.com/ipython/ipython/pull/6463>`__
- Creating a widget registry on the Python side.
  `#6493 <https://github.com/ipython/ipython/pull/6493>`__
- Allow widget views to be loaded from require modules
  `#6494 <https://github.com/ipython/ipython/pull/6494>`__
- Fix Issue #6530
  `#6532 <https://github.com/ipython/ipython/pull/6532>`__
- Make comm manager (mostly) independent of InteractiveShell
  `#6540 <https://github.com/ipython/ipython/pull/6540>`__
- Add semantic classes to top-level containers for single widgets
  `#6609 <https://github.com/ipython/ipython/pull/6609>`__
- Selection Widgets: forcing 'value' to be in 'values'
  `#6617 <https://github.com/ipython/ipython/pull/6617>`__
- Allow widgets to be constructed from Javascript
  `#6664 <https://github.com/ipython/ipython/pull/6664>`__
- Output widget
  `#6670 <https://github.com/ipython/ipython/pull/6670>`__
- Minor change in widgets.less to fix alignment issue
  `#6681 <https://github.com/ipython/ipython/pull/6681>`__
- Make Selection widgets respect values order.
  `#6747 <https://github.com/ipython/ipython/pull/6747>`__
- Widget persistence API
  `#6789 <https://github.com/ipython/ipython/pull/6789>`__
- Add promises to the widget framework.
  `#6818 <https://github.com/ipython/ipython/pull/6818>`__
- SelectMultiple widget
  `#6890 <https://github.com/ipython/ipython/pull/6890>`__
- Tooltip on toggle button
  `#6923 <https://github.com/ipython/ipython/pull/6923>`__
- Allow empty text box \*while typing\* for numeric widgets
  `#6943 <https://github.com/ipython/ipython/pull/6943>`__
- Ignore failure of widget MathJax typesetting
  `#6948 <https://github.com/ipython/ipython/pull/6948>`__
- Refactor the do\_diff and manual child view lists into a separate
  ViewList object
  `#6990 <https://github.com/ipython/ipython/pull/6990>`__
- Add warning to widget namespace import.
  `#7107 <https://github.com/ipython/ipython/pull/7107>`__
- lazy load widgets
  `#7120 <https://github.com/ipython/ipython/pull/7120>`__
- Fix padding of widgets.
  `#7139 <https://github.com/ipython/ipython/pull/7139>`__
- Persist widgets across page refresh
  `#7163 <https://github.com/ipython/ipython/pull/7163>`__
- Make the widget experimental error a real python warning
  `#7200 <https://github.com/ipython/ipython/pull/7200>`__
- Make the widget error message shorter and more understandable.
  `#7201 <https://github.com/ipython/ipython/pull/7201>`__
- Make the widget warning brief and easy to filter
  `#7204 <https://github.com/ipython/ipython/pull/7204>`__
- Add visual cue for widgets with dead comms
  `#7227 <https://github.com/ipython/ipython/pull/7227>`__
- Widget values as positional arguments
  `#7260 <https://github.com/ipython/ipython/pull/7260>`__
- Remove the popup widget
  `#7341 <https://github.com/ipython/ipython/pull/7341>`__
- document and validate link, dlink
  `#7468 <https://github.com/ipython/ipython/pull/7468>`__
- Document interact 5637
  `#7525 <https://github.com/ipython/ipython/pull/7525>`__
- Update some broken examples of using widgets
  `#7547 <https://github.com/ipython/ipython/pull/7547>`__
- Use Output widget with Interact
  `#7554 <https://github.com/ipython/ipython/pull/7554>`__
- don't send empty execute\_result messages
  `#7560 <https://github.com/ipython/ipython/pull/7560>`__
- Validation on the python side
  `#7602 <https://github.com/ipython/ipython/pull/7602>`__
- only show prompt overlay if there's a prompt
  `#7661 <https://github.com/ipython/ipython/pull/7661>`__
- Allow predictate to be used for comparison in selection widgets
  `#7674 <https://github.com/ipython/ipython/pull/7674>`__
- Fix widget view persistence.
  `#7680 <https://github.com/ipython/ipython/pull/7680>`__
- Revert "Use Output widget with Interact"
  `#7703 <https://github.com/ipython/ipython/pull/7703>`__
