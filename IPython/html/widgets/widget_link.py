"""Link and DirectionalLink classes.

Propagate changes between widgets on the javascript side
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .widget import Widget
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils.traitlets import Unicode, Tuple, List,Instance, TraitError

class WidgetTraitTuple(Tuple):
    """Traitlet for validating a single (Widget, 'trait_name') pair"""
    
    def __init__(self, **kwargs):
        super(WidgetTraitTuple, self).__init__(Instance(Widget), Unicode, **kwargs)
    
    def validate_elements(self, obj, value):
        value = super(WidgetTraitTuple, self).validate_elements(obj, value)
        widget, trait_name = value
        trait = widget.traits().get(trait_name)
        trait_repr = "%s.%s" % (widget.__class__.__name__, trait_name)
        # Can't raise TraitError because the parent will swallow the message
        # and throw it away in a new, less informative TraitError
        if trait is None:
            raise TypeError("No such trait: %s" % trait_repr)
        elif not trait.get_metadata('sync'):
            raise TypeError("%s cannot be synced" % trait_repr)
        
        return value


class Link(Widget):
    """Link Widget
    
    one trait:
    widgets, a list of (widget, 'trait_name') tuples which should be linked in the frontend.
    """
    _model_name = Unicode('LinkModel', sync=True)
    widgets = List(WidgetTraitTuple, sync=True)

    def __init__(self, widgets, **kwargs):
        if len(widgets) < 2:
            raise TypeError("Require at least two widgets to link")
        kwargs['widgets'] = widgets
        super(Link, self).__init__(**kwargs)

    # for compatibility with traitlet links
    def unlink(self):
        self.close()


@skip_doctest
def jslink(*args):
    """Link traits from different widgets together on the frontend so they remain in sync.

    Parameters
    ----------
    *args : two or more (Widget, 'trait_name') tuples that should be kept in sync.

    Examples
    --------

    >>> c = link((widget1, 'value'), (widget2, 'value'), (widget3, 'value'))
    """
    return Link(widgets=args)


class DirectionalLink(Widget):
    """A directional link
    
    source: a (Widget, 'trait_name') tuple for the source trait
    targets: one or more (Widget, 'trait_name') tuples that should be updated
    when the source trait changes.
    """
    _model_name = Unicode('DirectionalLinkModel', sync=True)
    targets = List(WidgetTraitTuple, sync=True)
    source = WidgetTraitTuple(sync=True)

    # Does not quite behave like other widgets but reproduces
    # the behavior of IPython.utils.traitlets.directional_link
    def __init__(self, source, targets, **kwargs):
        if len(targets) < 1:
            raise TypeError("Require at least two widgets to link")
        
        kwargs['source'] = source
        kwargs['targets'] = targets
        super(DirectionalLink, self).__init__(**kwargs)

    # for compatibility with traitlet links
    def unlink(self):
        self.close()

@skip_doctest
def jsdlink(source, *targets):
    """Link the trait of a source widget with traits of target widgets in the frontend.

    Parameters
    ----------
    source : a (Widget, 'trait_name') tuple for the source trait
    *targets : one or more (Widget, 'trait_name') tuples that should be updated
    when the source trait changes.

    Examples
    --------

    >>> c = dlink((src_widget, 'value'), (tgt_widget1, 'value'), (tgt_widget2, 'value'))
    """
    return DirectionalLink(source=source, targets=targets)

