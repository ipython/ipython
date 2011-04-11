"""Code that shows off the IPython display logic.
"""

from IPython.core.display import (
    display, display_pretty, display_html,
    display_svg, display_json
)

class Circle(object):

    def __init__(self, radius):
        self.radius = radius

    def _repr_pretty_(self, p, cycle):
        p.text(u"\u25CB")

    __pretty__ = _repr_pretty_

    def _repr_html_(self):
        return "<h1>Cirle: radius=%s</h1>" % self.radius

    def _repr_svg_(self):
        return """<svg>
<circle cx="100" cy="50" r="40" stroke="black" stroke-width="2" fill="red"/>
</svg>"""

